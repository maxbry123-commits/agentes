from datasets import load_dataset


def filter_problems(x):  # NOTE: not filtering out [links, grid, plot]
    for keyword in ["figure", "diagram", "jpeg", "png", "jpg", "svg", "answer:"]:
        if keyword in x["problem"].lower():
            return False
    if x["problem"].lower().startswith("a)") and "b)" in x["problem"].lower():
        return False
    if x["solution"] is None:
        return False
    if x["solution"] == "":
        return False
    if "\\boxed{}" in x["solution"].lower():
        return False
    if "\\boxed{" not in x["solution"].lower():
        return False
    return True


if __name__ == "__main__":
    for source in ["amc_aime", "olympiads", "aops_forum", "math"]:
        print(f"##### {source} #####")
        full = load_dataset("AI-MO/NuminaMath-CoT", split="train").filter(
            lambda x: x["source"] == source
        )

        figures = full.filter(lambda x: "figure" in x["problem"])
        if len(figures) > 0:
            figures.add_column("filter", ["figures"] * len(figures))
        print(
            "figures: ",
            len(figures),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_figures",
        )

        diagrams = full.filter(lambda x: "diagram" in x["problem"])
        if len(diagrams) > 0:
            diagrams.add_column("filter", ["diagrams"] * len(diagrams))
        print(
            "diagrams: ",
            len(diagrams),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_diagrams",
        )

        links = full.filter(lambda x: "http" in x["problem"])
        if len(links) > 0:
            links.add_column("filter", ["links"] * len(links))
        print(
            "links: ",
            len(links),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_links",
        )

        imgs = full.filter(
            lambda x: any(
                img in x["problem"].lower() for img in ["jpeg", "png", "jpg", "svg"]
            )
        )
        if len(imgs) > 0:
            imgs.add_column("filter", ["imgs"] * len(imgs))
        print(
            "imgs: ",
            len(imgs),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_imgs",
        )

        multipart = full.filter(
            lambda x: x["problem"].lower().startswith("a)")
            and "b)" in x["problem"].lower()
        )
        if len(multipart) > 0:
            multipart.add_column("filter", ["multipart"] * len(multipart))
        print(
            "multipart: ",
            len(multipart),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_multipart",
        )

        answer = full.filter(lambda x: "answer:" in x["problem"].lower())
        if len(answer) > 0:
            answer.add_column("filter", ["answer"] * len(answer))
        print(
            "answer: ",
            len(answer),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_answer",
        )

        grid = full.filter(lambda x: "grid" in x["problem"].lower())
        if len(grid) > 0:
            grid.add_column("filter", ["grid"] * len(grid))
        print(
            "grid: ",
            len(grid),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_grid",
        )

        plot = full.filter(lambda x: "plot" in x["problem"].lower())
        if len(plot) > 0:
            plot.add_column("filter", ["plot"] * len(plot))
        print(
            "plot: ",
            len(plot),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_plot",
        )

        empty_boxed = full.filter(lambda x: "\\boxed{}" in x["solution"].lower())
        if len(empty_boxed) > 0:
            empty_boxed.add_column("filter", ["empty_boxed"] * len(empty_boxed))
        print(
            "empty_boxed: ",
            len(empty_boxed),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_empty_boxed",
        )

        no_boxed = full.filter(lambda x: "\\boxed{" not in x["solution"].lower())
        if len(no_boxed) > 0:
            no_boxed.add_column("filter", ["no_boxed"] * len(no_boxed))
        print(
            "no_boxed: ",
            len(no_boxed),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_no_boxed",
        )

        no_solution = full.filter(
            lambda x: x["solution"] is None or x["solution"] == ""
        )
        if len(no_solution) > 0:
            no_solution.add_column("filter", ["no_solution"] * len(no_solution))
        print(
            "no_solution: ",
            len(no_solution),
            f"https://huggingface.co/datasets/mlfoundations-dev/{source}_no_solution",
        )

        filtered = full.filter(filter_problems)
        print(f"original {source}: ", len(full))
        print(f"filtered {source}: ", len(filtered))

        figures.push_to_hub(f"mlfoundations-dev/{source}_figures")
        diagrams.push_to_hub(f"mlfoundations-dev/{source}_diagrams")
        imgs.push_to_hub(f"mlfoundations-dev/{source}_imgs")
        links.push_to_hub(f"mlfoundations-dev/{source}_links")
        multipart.push_to_hub(f"mlfoundations-dev/{source}_multipart")
        answer.push_to_hub(f"mlfoundations-dev/{source}_answer")
        grid.push_to_hub(f"mlfoundations-dev/{source}_grid")
        plot.push_to_hub(f"mlfoundations-dev/{source}_plot")
        empty_boxed.push_to_hub(f"mlfoundations-dev/{source}_empty_boxed")
        no_boxed.push_to_hub(f"mlfoundations-dev/{source}_no_boxed")
        filtered.push_to_hub(f"mlfoundations-dev/{source}_filtered")

"""
##### amc_aime #####
figures:  132 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_figures
diagrams:  39 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_diagrams
links:  258 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_links
imgs:  27 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_imgs
multipart:  0 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_multipart
answer:  0 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_answer
grid:  30 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_grid
plot:  8 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_plot
empty_boxed:  0 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_empty_boxed
no_boxed:  145 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_no_boxed
no_solution:  0 https://huggingface.co/datasets/mlfoundations-dev/amc_aime_no_solution
original amc_aime:  4070
filtered amc_aime:  3736

##### olympiads #####
figures:  4075 https://huggingface.co/datasets/mlfoundations-dev/olympiads_figures
diagrams:  1859 https://huggingface.co/datasets/mlfoundations-dev/olympiads_diagrams
links:  422 https://huggingface.co/datasets/mlfoundations-dev/olympiads_links
imgs:  421 https://huggingface.co/datasets/mlfoundations-dev/olympiads_imgs
multipart:  1078 https://huggingface.co/datasets/mlfoundations-dev/olympiads_multipart
answer:  150 https://huggingface.co/datasets/mlfoundations-dev/olympiads_answer
grid:  2041 https://huggingface.co/datasets/mlfoundations-dev/olympiads_grid
plot:  226 https://huggingface.co/datasets/mlfoundations-dev/olympiads_plot
empty_boxed:  9650 https://huggingface.co/datasets/mlfoundations-dev/olympiads_empty_boxed
no_boxed:  10764 https://huggingface.co/datasets/mlfoundations-dev/olympiads_no_boxed
no_solution:  0 https://huggingface.co/datasets/mlfoundations-dev/olympiads_no_solution
original olympiads:  150563
filtered olympiads:  122742

##### aops_forum #####
figures:  397 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_figures
diagrams:  144 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_diagrams
links:  619 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_links
imgs:  338 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_imgs
multipart:  107 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_multipart
answer:  1 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_answer
grid:  344 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_grid
plot:  23 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_plot
empty_boxed:  8 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_empty_boxed
no_boxed:  11789 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_no_boxed
no_solution:  0 https://huggingface.co/datasets/mlfoundations-dev/aops_forum_no_solution
original aops_forum:  30192
filtered aops_forum:  17755

##### math #####
figures:  91 https://huggingface.co/datasets/mlfoundations-dev/math_figures
diagrams:  93 https://huggingface.co/datasets/mlfoundations-dev/math_diagrams
links:  0 https://huggingface.co/datasets/mlfoundations-dev/math_links
imgs:  0 https://huggingface.co/datasets/mlfoundations-dev/math_imgs
multipart:  0 https://huggingface.co/datasets/mlfoundations-dev/math_multipart
answer:  0 https://huggingface.co/datasets/mlfoundations-dev/math_answer
grid:  48 https://huggingface.co/datasets/mlfoundations-dev/math_grid
plot:  25 https://huggingface.co/datasets/mlfoundations-dev/math_plot
empty_boxed:  0 https://huggingface.co/datasets/mlfoundations-dev/math_empty_boxed
no_boxed:  0 https://huggingface.co/datasets/mlfoundations-dev/math_no_boxed
no_solution:  0 https://huggingface.co/datasets/mlfoundations-dev/math_no_solution
original math:  7477
filtered math:  7289

"""
