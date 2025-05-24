def process_single_layout_pdf(
    filename: str, config: ProcessingConfig
) -> Tuple[bool, float, str, List[Tuple[str, str]]]:
    """Process a single PDF file in layout-preserving mode.

    Args:
        filename: Name of the PDF file to process
        config: Processing configuration

    Returns:
        tuple: (success: bool, processing_time: float, error_message: str, log_messages: list)
    """
    # Setup logging for this process
    logger = setup_logging(config.log_path, config.quiet, is_worker=True)
    log_messages = []

    try:
        pdf_path = os.path.join(config.source_dir, filename)
        base_name = os.path.splitext(filename)[0]
        out_path = os.path.join(config.pdf_dir, f"{base_name}_ocr.pdf")
        temp_pdf_path = os.path.join(config.pdf_dir, f"{base_name}_temp.pdf")

        total_time = 0.0

        # Get total number of pages
        with open(pdf_path, "rb") as f:
            pdf = PdfReader(f)
            total_pages = len(pdf.pages)

        # Process each page with OCR
        pdf_pages = []

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            with timing_context("OCR processing", None) as get_ocr_time:
                # Configure tqdm to write to /dev/null in quiet mode
                tqdm_file = (
                    open(os.devnull, "w")
                    if (config.quiet or config.summary)
                    else sys.stderr
                )

                try:
                    if config.batch_size is None:
                        # Process all pages at once
                        pages_batch = convert_from_path(
                            pdf_path,
                            dpi=200,
                            use_pdftocairo=True,
                        )

                        # Process each page
                        for page_num, page_img in enumerate(
                            tqdm(
                                pages_batch,
                                desc="Processing pages",
                                unit="page",
                                file=tqdm_file,
                                disable=config.quiet or config.summary,
                                leave=False,
                            )
                        ):
                            # Save image to temporary file with high quality for OCR
                            img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                            page_img.save(img_path, "PNG")

                            # Generate PDF with OCR using tesseract
                            pdf_path_base = os.path.join(temp_dir, f"page_{page_num}")
                            cmd = [
                                "tesseract",
                                img_path,
                                pdf_path_base,
                                "-l",
                                config.lang,
                                "--dpi",
                                "200",
                                "pdf",
                            ]
                            subprocess.run(cmd, check=True, capture_output=True)

                            # Read generated PDF
                            with open(f"{pdf_path_base}.pdf", "rb") as f:
                                # Ensure we have enough slots in pdf_pages
                                while len(pdf_pages) <= page_num:
                                    pdf_pages.append(None)
                                pdf_pages[page_num] = f.read()

                        # Explicitly free memory
                        del pages_batch
                    else:
                        # Process pages in batches
                        for batch_start in tqdm(
                            range(1, total_pages + 1, config.batch_size),
                            desc="Processing batches",
                            unit="batch",
                            file=tqdm_file,
                            disable=config.quiet or config.summary,
                            leave=False,
                        ):
                            batch_end = min(
                                batch_start + config.batch_size - 1, total_pages
                            )

                            # Convert batch of pages to images
                            pages_batch = convert_from_path(
                                pdf_path,
                                dpi=200,
                                first_page=batch_start,
                                last_page=batch_end,
                                use_pdftocairo=True,
                            )

                            # Process each page in the batch
                            for page_num, page_img in enumerate(
                                tqdm(
                                    pages_batch,
                                    desc=f"Pages {batch_start}-{batch_end}",
                                    unit="page",
                                    file=tqdm_file,
                                    disable=config.quiet or config.summary,
                                    leave=False,
                                    position=1,
                                ),
                                start=batch_start - 1,
                            ):
                                # Save image to temporary file with high quality for OCR
                                img_path = os.path.join(temp_dir, f"page_{page_num}.png")
                                page_img.save(img_path, "PNG")

                                # Generate PDF with OCR using tesseract
                                pdf_path_base = os.path.join(temp_dir, f"page_{page_num}")
                                cmd = [
                                    "tesseract",
                                    img_path,
                                    pdf_path_base,
                                    "-l",
                                    config.lang,
                                    "--dpi",
                                    "200",
                                    "pdf",
                                ]
                                subprocess.run(cmd, check=True, capture_output=True)

                                # Read generated PDF
                                with open(f"{pdf_path_base}.pdf", "rb") as f:
                                    # Ensure we have enough slots in pdf_pages
                                    while len(pdf_pages) <= page_num:
                                        pdf_pages.append(None)
                                    pdf_pages[page_num] = f.read()

                            # Explicitly free memory
                            del pages_batch

                finally:
                    # Close tqdm file if it was opened
                    if tqdm_file != sys.stderr:
                        tqdm_file.close()

            total_time += get_ocr_time.duration
            log_messages = [
                (
                    "INFO",
                    f"  OCR processing took {get_ocr_time.duration:.2f} seconds",
                )
            ]

        # Combine all pages into a single PDF
        with PdfWriter() as pdf_writer:
            for page_num, page_pdf in enumerate(pdf_pages):
                if page_pdf:
                    page = PdfReader(page_pdf).pages[0]
                    pdf_writer.add_page(page)

        # Save the combined PDF
        with open(out_path, "wb") as f:
            pdf_writer.write(f)

        return True, total_time, "", log_messages
    except Exception as e:
        return False, 0.0, str(e), []

def process_multiple_layout_pdf(
    pdf_files: List[str], config: ProcessingConfig, max_workers: int
) -> Tuple[bool, float, str, List[Tuple[str, str]]]:
    """Process multiple PDF files in layout-preserving mode.

    Args:
        pdf_files: List of PDF file names to process
        config: Processing configuration
        max_workers: Maximum number of worker threads to use

    Returns:
        tuple: (success: bool, processing_time: float, error_message: str, log_messages: list)
    """
    # Setup logging for this process
    logger = setup_logging(config.log_path, config.quiet, is_worker=True)
    log_messages = []

    try:
        log_message(
            logger,
            "INFO",
            f"Processing {len(pdf_files)} files using {max_workers} workers",
            quiet=config.quiet
            or config.summary,  # Hide in both quiet and summary modes
        )
        if config.batch_size is not None:
            log_message(
                logger,
                "INFO",
                f"Batch-size: {config.batch_size} pages",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )
        log_message(
            logger,
            "INFO",
            "",
            quiet=config.quiet
            or config.summary,  # Hide in both quiet and summary modes
        )

        total_time = 0.0

        # Process each file in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_single_layout_pdf, filename, config)
                for filename in pdf_files
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Combine results
        success = all(result[0] for result in results)
        processing_time = sum(result[1] for result in results)
        error_message = "" if success else "One or more processing errors occurred"
        log_messages = [
            (
                "INFO",
                f"Processing time: {processing_time:.2f} seconds",
            )
        ] + [
            (
                "INFO",
                f"  {filename}: {result[2]}",
            )
            for filename, result in zip(pdf_files, results)
        ]

        return success, processing_time, error_message, log_messages 

def process_pdfs_with_ocr(config: ProcessingConfig, logger) -> None:
    """Process PDF files with OCR and convert to selected formats.

    This function processes each PDF file in the source directory with OCR
    and generates the requested output formats (PDF, DOCX, HTML, EPUB).

    Key features:
    - Parallel processing with configurable number of workers
    - Progress tracking and logging
    - Multiple output formats
    - Error handling and reporting
    - Graceful shutdown support

    Args:
        config: Processing configuration
        logger: Logger instance
    """
    try:
        # Validate configuration
        config.validate(logger)

        # Show EPUB/DOCX dependency warning
        if config.generate_epub and not config.generate_docx:
            log_message(
                logger,
                "WARNING",
                "EPUB generation requires DOCX format. Enabling DOCX generation automatically.",
                quiet=config.quiet,  # Show in summary mode
            )
            config.generate_docx = True

        # Create output directories
        if config.generate_pdf:
            os.makedirs(config.pdf_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"PDF folder created - {config.pdf_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_docx:
            os.makedirs(config.docx_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"DOCX folder created - {config.docx_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_html:
            os.makedirs(config.html_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"HTML folder created - {config.html_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        if config.generate_epub:
            os.makedirs(config.epub_dir, exist_ok=True)
            log_message(
                logger,
                "DEBUG",
                f"EPUB folder created - {config.epub_dir}",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        log_message(
            logger, "DEBUG", "", quiet=config.quiet or config.summary
        )  # Empty line after directories

        # Get list of PDF files
        pdf_files = sorted(
            f for f in os.listdir(config.source_dir) if f.lower().endswith(".pdf")
        )
        if not pdf_files:
            log_message(
                logger, "WARNING", "No PDF files found!", quiet=config.quiet
            )  # Show in summary mode
            return

        # Process files in parallel
        with timing_context("Total execution", logger) as get_total_time:
            # Use configured number of workers
            max_workers = config.workers
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )
            log_message(
                logger,
                "INFO",
                f"Processing {len(pdf_files)} files using {max_workers} workers",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )
            if config.batch_size is not None:
                log_message(
                    logger,
                    "INFO",
                    f"Batch-size: {config.batch_size} pages",
                    quiet=config.quiet
                    or config.summary,  # Hide in both quiet and summary modes
                )
            log_message(
                logger,
                "INFO",
                "",
                quiet=config.quiet
                or config.summary,  # Hide in both quiet and summary modes
            )

        # Process each file in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(process_single_layout_pdf, filename, config)
                for filename in pdf_files
            ]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Combine results
        success = all(result[0] for result in results)
        processing_time = sum(result[1] for result in results)
        error_message = "" if success else "One or more processing errors occurred"
        log_messages = [
            (
                "INFO",
                f"Processing time: {processing_time:.2f} seconds",
            )
        ] + [
            (
                "INFO",
                f"  {filename}: {result[2]}",
            )
            for filename, result in zip(pdf_files, results)
        ]

        return success, processing_time, error_message, log_messages 