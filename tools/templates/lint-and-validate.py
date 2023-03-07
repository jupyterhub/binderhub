#!/usr/bin/env python3
"""
Lints and validates the chart's template files and their rendered output without
any cluster interaction. For this script to function, you must install yamllint.

USAGE:

  tools/templates/lint-and-validate.py

DEPENDENCIES:

yamllint: https://github.com/adrienverge/yamllint

  pip install yamllint
"""

import argparse
import os
import pipes
import subprocess
import sys

os.chdir(os.path.dirname(sys.argv[0]))


def check_call(cmd, **kwargs):
    """Run a subcommand and exit if it fails"""
    try:
        subprocess.check_call(cmd, **kwargs)
    except subprocess.CalledProcessError as e:
        print(
            "`{}` exited with status {}".format(
                " ".join(map(pipes.quote, cmd)),
                e.returncode,
            ),
            file=sys.stderr,
        )
        sys.exit(e.returncode)


def lint(yamllint_config, values, output_dir, strict, debug):
    """Calls `helm lint`, `helm template`, and `yamllint`."""

    print("### Clearing output directory")
    check_call(["mkdir", "-p", output_dir])
    check_call(["rm", "-rf", f"{output_dir}/*"])

    print("### Linting started")
    print("### 1/3 - helm lint: lint helm templates")
    helm_lint_cmd = ["helm", "lint", "../../jupyterhub", f"--values={values}"]
    if strict:
        helm_lint_cmd.append("--strict")
    if debug:
        helm_lint_cmd.append("--debug")
    check_call(helm_lint_cmd)

    print("### 2/3 - helm template: generate kubernetes resources")
    helm_template_cmd = [
        "helm",
        "template",
        "../../jupyterhub",
        f"--values={values}",
        f"--output-dir={output_dir}",
    ]
    if debug:
        helm_template_cmd.append("--debug")
    check_call(helm_template_cmd)

    print("### 3/3 - yamllint: yaml lint generated kubernetes resources")
    check_call(["yamllint", "-c", yamllint_config, output_dir])

    print()
    print(
        "### Linting and validation of helm templates and generated kubernetes resources OK!"
    )


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--debug",
        action="store_true",
        help="Run helm lint and helm template with the --debug flag",
    )
    argparser.add_argument(
        "--strict",
        action="store_true",
        help="Run helm lint with the --strict flag",
    )
    argparser.add_argument(
        "--values",
        default="lint-and-validate-values.yaml",
        help="Specify Helm values in a YAML file (can specify multiple)",
    )
    argparser.add_argument(
        "--output-dir",
        default="rendered-templates",
        help="Output directory for the rendered templates. Warning: content in this will be wiped.",
    )
    argparser.add_argument(
        "--yamllint-config",
        default="yamllint-config.yaml",
        help="Specify a yamllint config",
    )

    args = argparser.parse_args()

    lint(
        args.yamllint_config,
        args.values,
        args.output_dir,
        args.strict,
        args.debug,
    )
