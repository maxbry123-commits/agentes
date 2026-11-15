from eval.local.run_eval import EvalRunner


def test_eval_worker_accepts_controller_ingress_arguments():
    args = EvalRunner.create_parser().parse_args(
        [
            "--harbor_config",
            "config.yaml",
            "--dataset_path",
            "tasks",
            "--ingress_mode",
            "controller",
            "--ingress_host",
            "https://iris.oa.dev",
        ]
    )

    assert args.ingress_mode == "controller"
    assert args.ingress_host == "https://iris.oa.dev"
