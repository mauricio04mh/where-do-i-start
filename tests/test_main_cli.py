from src import main


def test_parse_args_accepts_space_separated_experiment_algorithms(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "main.py",
            "--run-experiments",
            "--experiment-algorithms",
            "greedy",
            "branch_and_bound",
            "simulated_annealing",
            "ant_colony",
        ],
    )

    args = main.parse_args()

    assert main.parse_experiment_algorithms(args.experiment_algorithms) == [
        "greedy",
        "branch_and_bound",
        "simulated_annealing",
        "ant_colony",
    ]


def test_parse_experiment_options_accept_comma_separated_strings() -> None:
    assert main.parse_experiment_algorithms("greedy,ant_colony") == [
        "greedy",
        "ant_colony",
    ]
    assert main.parse_experiment_seeds("42,99") == [42, 99]
