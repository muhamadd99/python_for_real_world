import email
import quopri
from pathlib import Path

RESET = "\033[0m"
YELLOW = "\033[38;5;208m"
MAGENTA = "\033[38;5;90m"

def ingest_all_mhtml(input_dir, output_dir):
#take path 
	input_path = Path(input_dir)
	output_path = Path(output_dir)
	output_path.mkdir(parents=True, exist_ok=True) #parents=True behaved like mkdir -p. means that if no folder it create. 2. exist_ok=true means that if exists it will keep quiet

	print("🥉 Bronze:...")
	#check if directory exists, confirm directory and has files for idempotency. failure will gives empty list
	files = list(input_path.glob("*.mhtml")) #files is a list of path objects
	if not files:
		print("No source files found")
		return

	success_count = 0
	failed_count = 0

	#for loop and decode everything(quopri)
	for file_path in files: #file_path is a path object
			success = ingest_single_file(file_path, output_path)

			if success:
				print(f"✅ Extracted: {file_path.name}")
				success_count += 1
			else:
				print(f"⚠️ No HTML content found in: {file_path.name}")
				failed_count += 1

	print("\n📊 Bronze Summary:")
	print(f"Total: {MAGENTA}{success_count + failed_count}{RESET} {YELLOW}|{RESET} Extracted: {MAGENTA}{success_count}{RESET} {YELLOW}|{RESET} Failed: {MAGENTA}{failed_count}{RESET}")

def ingest_single_file(file_path: Path, output_path: Path):
	with open(file_path, "r") as f:
		msg = email.message_from_file(f) #msg becomes emailmessage objec
		for part in msg.walk():
			content_type = part.get_content_type()
			if content_type == "text/html":
				payload = part.get_payload(decode=True) #decode true ensure that our format is correctly decoded

				#create output filename
				output_file = output_path/f"{file_path.stem}.html"
				#write into output file
				with open(output_file, "wb") as f_out:
					f_out.write(payload)
				return True
		return False