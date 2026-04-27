
# Email List Generator for Gmail Backup Archives with Wordpress Data

This script parses your [Got-Your-Back (GYB)](https://github.com/GAM-team/got-your-back) Gmail backups to generate a CSV of names and email addresses matching your criteria.

How it Works
------------
* GYB Downloads my emails to .eml files on my computer once per day.  A nested folder structure is populated with emails.
* The python script contains a number of configuration variables for setting the date range to search through, the location of the email backups, the output CSV file name, search terms to identify, and spam terms to indicate that a message should be ignored.
* The script iterates through all the email to find the requested search terms (indicating the email came from my website as a contact or a comment).
* A name and email is extracted from each email that matches the search terms, and is added to a list.
* The list is then checked for duplicate email addresses, which are removed.
* Non-duplicate email addresses are validated for correct syntax and DNS deliverability (MX record lookup) using the [email-validator](https://github.com/JoshData/python-email-validator) library.
* If the address is determined to be valid, then it is appended to a CSV output file.

Notes
-----
* Update the "CONFIGURATION OPTIONS" in the script to match your search scenario. You can provide an arbitrary list of subject search terms by editing the `subject_search_terms` list in the script.
* This script assumes Python 3.x. It was originally written for Windows, but should work cross-platform with minor adjustments.
* GYB was used to download my email archive: https://github.com/GAM-team/got-your-back
* The [email-validator](https://github.com/JoshData/python-email-validator) library is used for email syntax and deliverability validation.
* This Script has been written by [Jeremy Blum](https://www.jeremyblum.com) and is released under the GPL v3.  A copy of the GPL is included within this Repo.  Kindly share your improvements to this script, and maintain attribution to the original author (me).