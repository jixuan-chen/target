from .ui.argparse import main

parser = main()
args = parser.parse_args()
if "path" in args:
    if args.path:
        from example.generate import generate_example

        if args.metblu and args.empty:
            parser.error("--empty and --obs cannot be used together.")

        generate_example(
            path=args.path,
            site_name=args.site,
            run_name=args.run,
            obs=args.metblu,
            grid=args.grid,
            empty=args.empty
        )

    else:
        parser._subparsers._group_actions[0].choices['gen'].print_help()
elif "conf" in args:
    if args.conf:

        from scripts.toolkit import Target

        tar = Target(args.conf, args.progress)
        tar.load_config()
        tar.run_simulation(save_csv=args.save_csv)

        if args.plot_ts:
            tar.plot_val_ts()

        if args.plot_ta:
            tar.plot_val_ta()

        if args.plot_gis:
            tar.plot_gis()

        tar.save_simulation_parameters()
    else:
        parser._subparsers._group_actions[0].choices['run'].print_help()
else:
    parser.print_help()
