parser.add_argument(
    "--batch-size",
    type=int,
    default=None,
    help="Number of pages to process in each batch (disabled by default). Use this to optimize memory usage for large PDFs.",
) 