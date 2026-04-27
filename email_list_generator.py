# This Script Searches through your "Got Your Back (GYB)" Gmail Backups
# to generate a list of email addresses/names that match specific criteria.
# This list is returned as a CSV File within this folder titled "emails.csv".
# This script is designed to run in Windows with Python 3.x.
#
# GYB can be found here: https://github.com/GAM-team/got-your-back
# The "Validate Email" Python Library is optionally used: https://github.com/SyrusAkbary/validate_email
# This script was authored by Jeremy Blum (https://www.jeremyblum.com). Licensed under GPL v3.

######
# CONFIGURATION OPTIONS
######
gyb_abs_directory       = 'C:\\gyb\\GYB-GMail-Backup-jeremy@jeremyblum.com\\'
start_year              = 2006
end_year                = 2026
spam_term               = 'Akismet: Spam'
output_file             = 'emails.csv'
validate_addresses      = False
subject_search_terms    = [
   'Subject: JeremyBlum.com Contact',
   'Subject: [JeremyBlum.com] Comment'
]

######
# IMPORT LIBRARIES
######
import datetime
import calendar
import os
import re
import csv
import email
from email.header import decode_header
from email import policy
if validate_addresses:
   from validate_email import validate_email

######
# ITERATE AND FIND EMAILS!
######


output = []

# Helper to decode email subject
def decode_subject(header):
   if not header:
      return ''
   decoded_parts = decode_header(header)
   subject = ''
   for part, encoding in decoded_parts:
      if isinstance(part, bytes):
         subject += part.decode(encoding or 'utf-8', errors='replace')
      else:
         subject += part
   return subject

# Helper to extract name/email from HTML contact form
def extract_contact_html(body):
   name_match = re.search(r'<b>Name:</b>\s*(.*?)<br>', body, re.IGNORECASE)
   email_match = re.search(r'<b>Email:</b>\s*([\w\.-]+@[\w\.-]+)', body, re.IGNORECASE)
   name = name_match.group(1).strip() if name_match else ''
   email_address = email_match.group(1).strip() if email_match else ''
   return name, email_address

# Helper to check if subject matches any search term (case-insensitive, partial)
def subject_matches(subject, search_terms):
   subject_lower = subject.lower()
   for term in search_terms:
      if term.lower().replace('subject:', '').strip() in subject_lower:
         return True
   return False


# Main extraction loop
for year in range(start_year, end_year + 1):
   for month in range(1, 13):
      for day in range(1, calendar.monthrange(year, month)[1] + 1):
         current_date = datetime.date(year, month, day)
         directory_path = os.path.join(
            gyb_abs_directory,
            current_date.strftime("%Y"),
            str(current_date.month),
            str(current_date.day)
         )
         if os.path.isdir(directory_path):
            print('Searching Emails from {0}'.format(current_date.strftime("%B %d, %Y")))
            for file_name in os.listdir(directory_path):
               file_path = os.path.join(directory_path, file_name)
               try:
                  with open(file_path, 'rb') as f:
                     msg = email.message_from_binary_file(f, policy=policy.default)
               except Exception as e:
                  print(f"\t{file_name}: Failed to parse email: {e}")
                  continue
               subject = decode_subject(msg.get('Subject', ''))
               if subject.strip().lower().startswith('re:'):
                  print(f"\t{file_name}: Skipped reply (subject: {subject})")
                  continue
               if not subject_matches(subject, subject_search_terms):
                  print(f"\t{file_name}: Skipped (subject: {subject})")
                  continue
               # Prefer name/email from headers
               from_header = msg.get('From', '')
               reply_to_header = msg.get('Reply-To', '')
               header_email = ''
               header_name = ''
               header_match = re.match(r'(.*)<([\w\.-]+@[\w\.-]+)>', from_header)
               if header_match:
                  header_name = header_match.group(1).strip(' "')
                  header_email = header_match.group(2).strip()
               elif '@' in from_header:
                  header_email = from_header.strip()
               # Prefer Reply-To if present and valid
               if reply_to_header and '@' in reply_to_header:
                  header_email = reply_to_header.strip()
               if header_email:
                  print(f"\t{file_name}: {header_name}, {header_email} (from header)")
                  output.append([header_name, header_email])
                  continue
               # Get body (prefer HTML, fallback to plain)
               body = ''
               if msg.is_multipart():
                  for part in msg.walk():
                     ctype = part.get_content_type()
                     if ctype == 'text/html':
                        body = part.get_content()
                        break
                     elif ctype == 'text/plain' and not body:
                        body = part.get_content()
               else:
                  body = msg.get_content()
               # Try HTML contact form extraction
               name, email_address = extract_contact_html(body)
               if name and email_address:
                  print(f"\t{file_name}: {name}, {email_address} (from body)")
                  output.append([name, email_address])
                  continue
               # Try legacy comment notification extraction (WordPress comments)
               author_result = re.search(r'Author : (.*) \(IP: ', body, re.DOTALL)
               name = ''
               email_address = ''
               if author_result:
                  author_info = author_result.group(0).split(' : ')
                  name = author_info[1].split(' (IP: ')[0]
               email_result = re.search(r'E-mail : (.*)\n', body, re.DOTALL)
               if email_result:
                  email_info = email_result.group(0).split(' : ')
                  email_address = email_info[1].strip()
               if name and email_address:
                  print(f"\t{file_name}: {name}, {email_address} (from body)")
                  output.append([name, email_address])
                  continue
               # Fallback: try to find first email in body
               fallback_email = None
               fallback_name = ''
               fallback_match = re.search(r'([\w\.-]+@[\w\.-]+)', body)
               if fallback_match:
                  fallback_email = fallback_match.group(1)
               if fallback_email:
                  print(f"\t{file_name}: {fallback_name}, {fallback_email} (fallback)")
                  output.append([fallback_name, fallback_email])
                  continue
               print(f"\t{file_name}: No name/email found (subject: {subject})")

######
# Remove Duplicates, Deal with Empty Emails, Check for SMTP mailbox existance, & Write to CSV
######
duplicates_removed = set()
count = 0
with open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
   writer = csv.writer(csv_file, dialect='excel')
   seen_emails = set()
   total_count = 0
   print('\nChecking Email Addresses and Writing to CSV File...')
   for entry in output:
      # Robust normalization for email and name
      raw_name, raw_email = entry[0], entry[1]
      # Extract email from <...> if present, else use as is
      email_match = re.search(r'<\s*([\w\.-]+@[\w\.-]+)\s*>', raw_email)
      if email_match:
         clean_email = email_match.group(1)
      else:
         clean_email = raw_email
      # Remove all leading/trailing quotes, whitespace, and angle brackets
      clean_email = clean_email.strip().strip('"').strip("'").replace('<','').replace('>','').strip()
      # Remove any trailing/leading quotes or whitespace from name
      clean_name = raw_name.strip().strip('"').strip("'")
      # If name is identical to email (with or without quotes), set to blank
      if clean_name.replace('"','').replace("'",'').strip() == clean_email:
         clean_name = ''
      # If email contains spaces, split and take the part that matches email format
      if ' ' in clean_email:
         for part in clean_email.split():
            if re.match(r'^[\w\.-]+@[\w\.-]+$', part):
               clean_email = part
               break
      # Final check: only add if clean_email is a valid-looking address
      if re.match(r'^[\w\.-]+@[\w\.-]+$', clean_email) and clean_email not in seen_emails:
         if validate_addresses:
            try:
               is_valid = validate_email(clean_email, verify=True)
            except Exception:
               is_valid = True  # Assume valid if SMTP server has issues.
         else:
            is_valid = True
         if is_valid:
            writer.writerow([clean_name, clean_email])
            seen_emails.add(clean_email)
            total_count += 1
            print('\tAdded {}!'.format(clean_email))
         else:
            print('\t{} is not a valid email address!'.format(clean_email))
   print('\nFound and Recorded {} unique Email Addresses into {}!'.format(total_count, output_file))
