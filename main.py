from bench.benchmarker import Benchmarker
from bench.system.system import system
from bench.logger import logger

import argparse
import asyncio

async def main():
    parser = argparse.ArgumentParser(description='My Simple CLI')

    parser.add_argument('--fast', action='store_true', default=False, help='Run a fast benchmark. This will do a single iteration on each dataset.')
    parser.add_argument('--full', action='store_true', default=False, help='Run the full benchmark. This will use the entire dataset. May take a long time')
    parser.add_argument('--verbose', action='store_true', default=False, help='Enable verbose output.')
    parser.add_argument('--debug', action='store_true', default=False, help='Enable debugging output.')
    parser.add_argument('--info', action='store_true', default=False, help='Display system information without running the benchmark')
    parser.add_argument('--download', action='store_true', default=False, help='Download the models and datasets without running the benchmark')
    parser.add_argument('--benchmark', type=str, default='all', help='Specify the benchmark to run. Comma separated list of language, hearing, vision, creation. Default is all.')
    # parser.add_argument('--recompile', action='store_true', default=False, help='Recompile the runtime cod')
    # parser.add_argument('--cpu', type=int, help='Specify the number of CPU cores to use')
    # parser.add_argument('--download_path', type=str, help='Specify the download path')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel('INFO')
    if args.debug:
        logger.setLevel('DEBUG')

    if args.info:
        system.print_sys_info()
        return

    benchmarker = Benchmarker(**vars(args))
    await benchmarker.download()

    if not args.download:
        benchmarker.benchmark(args.benchmark)

if __name__ == '__main__':
    asyncio.run(main())