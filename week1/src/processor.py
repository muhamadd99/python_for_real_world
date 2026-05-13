import json
from pydantic import BaseModel, ValidationError, Field
from bs4 import BeautifulSoup
from pathlib import Path

class JobListing(BaseModel):
	source_id: str = Field(min_length=1)
	job_title: str = Field(min_length=1)
	company: str = Field(min_length=1)
	description: str = Field(min_length=1)

def process_all_html(input_dir, output_dir):
	input_path = Path(input_dir)
	output_path = Path(output_dir)
	output_path.mkdir(parents=True, exist_ok=True)

	print("🥈 Silver: ...")
	files = list(input_path.glob("*.html"))
	if not files:
		print("No source files found")

	processed_count = 0
	skipped_count = 0

	for file_path in files:
		success = process_single_file(file_path, output_path)
		if success:
			processed_count += 1
		else:
			skipped_count += 1

	print(f"\n📊 Silver Summary:")
	print(f"Total: {len(files)} | Processed: {processed_count} | Skipped: {skipped_count}")


def process_single_file(file_path: Path, output_path: Path):
	with open(file_path, "r", encoding="utf-8") as f:
		soup = BeautifulSoup(f, "html.parser") #object of beautiful soup class
	try:
		# Find URL tag and take the last one
		url_tag = soup.find("meta", property="og:url")
		url_content = url_tag.get("content") if url_tag else None
		if not url_content:
			raise ValueError("source_id")
		source_id_extracted = url_content.rstrip("/").split("/")[-1]
		# Find data job title and strip the white space
		title_tag = soup.find(attrs={"data-automation": "job-detail-title"})
		if not title_tag:
			raise ValueError("job_title")
		job_title_extracted = title_tag.get_text(strip=True)
		# Find the company tag and strip whitespeace
		company_tag = soup.find(attrs={"data-automation": "advertiser-name"})
		if not company_tag:
			raise ValueError("company")
		company_extracted = company_tag.get_text(strip=True)
		# Find the description, clean unnecessary whitespace and put correct whitespace
		desc_tag = soup.find(attrs={"data-automation": "jobAdDetails"})
		if not desc_tag:
			raise ValueError("description")
		description_extracted = desc_tag.get_text(separator=" ", strip=True)
		# Validation using class contract
		job = JobListing (
			source_id=str(source_id_extracted),
			job_title= str(job_title_extracted),
			company= str(company_extracted),
			description= str(description_extracted)
		)
		# JSON Serialization
		output_file = output_path / f"{file_path.stem}.json"
		with open(output_file, "w", encoding="utf-8") as f: # utf-8 because it is universal, able to read emojis/languages
			#model_dump convert the pydantic object to a readable format
			json.dump(job.model_dump(), f, indent=2, ensure_ascii=False)
		print(f"✅ Processed: {file_path.name}")
		return True
	except (ValidationError, ValueError, TypeError) as e: #catching typeError when soup.find return none
		if "ValueError" in str(type(e)):
			missing_field = str(e)
		else:
			missing_field = "required fields"
		print(f"⚠️ missing {missing_field} in: {file_path.name}")
		return False
		
# desc_tag = soup.find("meta", property="og:description")
# description_content = desc_tag.get("content") if desc_tag else None
# if not description_content:
# 	raise ValueError("description")
# description_extracted = description_content.strip()