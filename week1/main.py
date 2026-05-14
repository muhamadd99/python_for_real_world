import sys #give access to system specific parameters and fx
from src.ingestor import ingest_all_mhtml
from src.processor import process_all_html
from src.loader import load_all_jsons
from src.profiler import run_data_profile

def main():
	if len(sys.argv) < 2:
		print("Usage: python main.py [ingest|process|load|profile|all]")
		return
	
	command = sys.argv[1]

	match command: #act like switch it compares command and the cases
		case "ingest":
			ingest_all_mhtml("data/0_source", "data/1_bronze")
		case "process":
			process_all_html("data/1_bronze", "data/2_silver")
		case "loaded":
			load_all_jsons("data/2_silver", "data/3_gold")
		case "profile":
			run_data_profile("data/3_gold/jobs.db")
		case "all":
			ingest_all_mhtml("data/0_source", "data/1_bronze")
			process_all_html("data/1_bronze", "data/2_silver")
			load_all_jsons("data/2_silver", "data/3_gold")
			run_data_profile("data/3_gold/jobs.db")
		case _:
			print(f"Unknown command:{command}") #by specifying f, it treats anything inside curly braces as code
	

if __name__ == "__main__":
    main()
