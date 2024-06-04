from benchmark import LanguageBenchmark
from downloader import downloader
from sys_info import system 

downloader.download()

system.print_sys_info()

# run benchmarks
lang_bench = LanguageBenchmark()
lang_bench.benchmark()