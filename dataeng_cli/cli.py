import json
import logging
import click
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

from .fetcher import UniProtFetcher
from .pipeline import SyncPipeline
from .validator import DataValidator
from .mock import generate_mock_uniprot_data
from .scheduler import run_scheduled_sync

# 结构化日志配置
logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("dataeng")
console = Console()

@click.group()
def main():
    """科研公共数据源采集与集成命令行工具 (dataeng-cli)"""
    pass

@main.command()
@click.option("--source", required=True, type=click.Choice(["uniprot", "pubchem"]), help="指定采集的数据源")
@click.option("--query", required=True, help="查询关键词或蛋白 ID")
@click.option("--output", default="./data/raw", help="原始数据保存路径")
@click.option("--mock", is_flag=True, help="开启 Mock 模式（离线演示）")
def fetch(source: str, query: str, output: str, mock: bool):
    """按关键词或 ID 从数据源拉取原始数据"""
    out_dir = Path(output)
    if mock:
        console.print("[yellow]⚠️ 开启 Mock 模式，生成离线测试数据...[/yellow]")
        raw_data = generate_mock_uniprot_data(query)
    else:
        if source == "uniprot":
            fetcher = UniProtFetcher()
            try:
                raw_data = fetcher.fetch(query)
            except Exception as e:
                console.print(f"[bold red]错误：[/bold red] {e}")
                return
        else:
            console.print(f"[bold red]暂不支持数据源 {source}[/bold red]")
            return

    fetcher = UniProtFetcher()
    saved_path = fetcher.save_raw(raw_data, out_dir, f"{source}_{query}")
    console.print(f"[green]✓ 采集成功！原始响应保存在: {saved_path}[/green]")

@main.command()
@click.option("--source", required=True, type=click.Choice(["uniprot"]), help="指定数据源")
@click.option("--since", help="增量同步起始日期 (YYYY-MM-DD)，若留空则自动读取上次水位线")
@click.option("--mock", is_flag=True, help="开启 Mock 模式（离线演示）")
@click.option("--schedule-mode", is_flag=True, help="开启内置定时调度演示模式")
def sync(source: str, since: str, mock: bool, schedule_mode: bool):
    """基于上次同步位置（Watermark）只拉增量数据，保证幂等"""
    pipeline = SyncPipeline()
    watermark = since or pipeline.get_watermark(source)
    
    def do_sync():
        console.print(f"[cyan]开始同步 [{source}] 数据，当前 Watermark: {watermark}[/cyan]")
        query = f"(date_modified:[{watermark} TO *])" if not mock else "insulin"
        
        if mock:
            raw_data = generate_mock_uniprot_data("sync_query")
        else:
            fetcher = UniProtFetcher()
            raw_data = fetcher.fetch(query)

        records = raw_data.get("results", [])
        added, updated, skipped = pipeline.process_and_deduplicate(records, source, Path("./data/processed"))
        
        # 更新 Watermark
        new_watermark = datetime.now().strftime("%Y-%m-%d")
        pipeline.set_watermark(source, new_watermark)

        console.print(f"[bold green]同步完成！新增: {added} | 更新: {updated} | 跳过(幂等去重): {skipped}[/bold green]")

    if schedule_mode:
        run_scheduled_sync(do_sync, interval_seconds=5, max_runs=2)
    else:
        do_sync()

@main.command()
@click.argument("data_dir", type=click.Path(exists=False))
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="json", help="输出格式")
@click.option("--output", "out_file", help="将结果输出至保存文件 (如 result.json)")
def validate(data_dir: str, fmt: str, out_file: str):
    """对已采集清洗的数据进行质量校验并输出结构化报告"""
    validator = DataValidator(Path(data_dir))
    report = validator.validate()

    report_str = json.dumps(report, ensure_ascii=False, indent=2)
    
    if fmt == "json":
        console.print_json(report_str)
    else:
        console.print(f"校验状态: {'[green]通过[/green]' if report['pass'] else '[red]未通过[/red]'}")
        console.print(f"详细报告: {report['comment']}")

    if out_file:
        Path(out_file).write_text(report_str, encoding="utf-8")
        console.print(f"[dim]报告已保存至: {out_file}[/dim]")

if __name__ == "__main__":
    main()
