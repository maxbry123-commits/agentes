from config import Config
from agent.workflow import Workflow
from agent.checkpoint import CheckpointManager
from agent.user_interface import CLIUserInterface
from datetime import datetime
import argparse
import hashlib
import os
import logging



def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # 清理 30 天前的旧日志
    _cleanup_old_logs(log_dir, days=30)

    # 生成带时间戳的日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"log_{timestamp}.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter_file = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    formatter_console = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter_file)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter_console)

    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _cleanup_old_logs(log_dir: str, days: int):
    """删除 days 天前的 .log 文件。"""
    cutoff = datetime.now().timestamp() - days * 86400
    for fname in os.listdir(log_dir):
        if fname.endswith(".log"):
            fpath = os.path.join(log_dir, fname)
            try:
                if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
            except OSError:
                pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CTF Agent / 渗透测试 Agent — 自动化安全测试助手")
    parser.add_argument(
        "--export-writeup",
        action="store_true",
        help="解题/测试成功后自动导出报告",
    )
    parser.add_argument(
        "--mode",
        choices=["ctf", "pentest"],
        help="运行模式: ctf=CTF解题, pentest=渗透测试 (不指定则交互选择)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="从上次中断的 checkpoint 继续（自动检测匹配的存档）",
    )
    parser.add_argument(
        "--auto", dest="auto_mode", action="store_true", default=None,
        help="强制自动模式（Agent 自主执行所有操作）",
    )
    parser.add_argument(
        "--manual", dest="auto_mode", action="store_false", default=None,
        help="强制手动模式（每一步需用户批准）",
    )
    parser.add_argument(
        "--interactive", action="store_true", default=False,
        help="启用交互模式选择（运行模式和手动/自动模式均通过终端提示选择）",
    )
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)
    config: dict = Config.load_config()
    ui = CLIUserInterface()

    if args.mode:
        mode = args.mode
    else:
        mode = "ctf"
        choice = ui.choose(
            "请选择运行模式:",
            ["CTF Agent", "渗透测试 Agent"],
        )
        mode = "pentest" if "渗透" in choice else "ctf"

    if mode == "ctf":
        ui.display("如题目中含有附件，请放附件文件到项目根目录的attachments文件夹下")
        ui.display("提示: 将题目文本写入 question.txt")
        ui.prompt_text("将题目文本放在Agent根目录下的question.txt回车以结束")
    else:
        ui.display("如有附件 (网络拓扑图/资产清单等)，请放入 attachments/ 目录")
        ui.display("提示: 将授权范围文档写入 scope.txt")
        ui.prompt_text("将授权范围文档写入 scope.txt 后回车以开始")

    input_file = "scope.txt" if mode == "pentest" else "question.txt"
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            task = f.read()
    except FileNotFoundError:
        logger.error(f"找不到 {input_file} 文件，请先将{'授权范围' if mode == 'pentest' else '题目文本'}写入该文件")
        exit(1)

    # ── Checkpoint 恢复 ──
    checkpoint_data = None
    if args.resume:
        ck_data = CheckpointManager.load(task, mode)
        if ck_data:
            checkpoint_data = ck_data
            logger.info("找到 checkpoint，将从第 %d 步继续", ck_data["meta"]["step_count"])
        else:
            logger.warning("未找到匹配的 checkpoint，将从头开始")

    logger.debug(f"{'授权范围' if mode == 'pentest' else '题目'}内容：{task}")
    # 处理 auto_mode：--auto/--manual 明确指定；未指定时 None（由 SolveAgent 内部交互选择）
    auto_mode = args.auto_mode
    if auto_mode is None:
        # 仅在 stdin 非 TTY 时强制自动模式（避免管道/重定向场景阻塞）
        import sys
        if not (hasattr(sys.stdin, 'isatty') and sys.stdin.isatty()):
            auto_mode = True
        # TTY 环境：auto_mode 保持 None，由 SolveAgent._select_mode() 弹出交互选择
    result = Workflow(config=config, mode=mode, ui=ui).solve(
        task, export_writeup=args.export_writeup, checkpoint_data=checkpoint_data,
        auto_mode=auto_mode, interactive=args.interactive,
    )
    logger.info(f"最终结果:{result}")


