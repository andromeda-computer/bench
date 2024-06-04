from benchmark import LanguageBenchmark
from downloader import download
from sys_info import system 

download() 
system.print_sys_info()

# run benchmarks
lang_bench = LanguageBenchmark()
lang_bench.benchmark()