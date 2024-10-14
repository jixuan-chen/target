from argparse import ArgumentParser

def main():

    parser = ArgumentParser(
        prog="target_py",
        description="The Air-temperature Response to Green/blue-infrastructure Evaluation Tool: an efficient and user-friendly model of city cooling! "
                    "Note that you should not use --generate-example in connection with any other flag."
    )

    parser.allow_abbrev = False

    subparser = parser.add_subparsers()
    parser_run = subparser.add_parser("run")
    parser_gen = subparser.add_parser("gen")

    requiredNamed = parser_run.add_argument_group('required arguments')
    requiredNamed.add_argument("-c", "--conf", help="pass a configuration file", required=True, default="")

    parser_run.add_argument("-p", "--progress", help="display model progress", action="store_true", default=False)
    parser_run.add_argument("--save-csv", help="save the result in csv files", action="store_true", default=False)
    parser_run.add_argument("--plot-ta", help="validate Ta for AWS", action="store_true", default=False)
    parser_run.add_argument("--plot-ts", help="validate Ts for AWS", action="store_true", default=False)
    parser_run.add_argument("--plot-gis", help="plot GIS for grid", action="store_true", default=False)


    parser_gen.add_argument("-p", "--path",
                            help="generates an example, pass a path to where the example should be generated",
                            default="")
    parser_gen.add_argument("--grid", help="generate grid example instead of the default no grid example",
                            action="store_true", default=False)
    parser_gen.add_argument("--obs", help="generate observations for model validation",
                            action="store_true", default=False)
    parser_gen.add_argument("--empty", help="generate folders structure, config file and parameters file only",
                            action="store_true", default=False)
    parser_gen.add_argument("--site", help="name of site", required=False, default=None)
    parser_gen.add_argument("--run", help="name of run", required=False, default=None)

    return parser
