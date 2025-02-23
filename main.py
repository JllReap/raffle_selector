import imaplib
import email
import os
from email.header import decode_header

# Account credentials
username = "leonid1988mail@mail.ru"  # Replace with your mail.ru email address
password = "n1FHYR44vRWz2eJCFwVy"  # Replace with your password or app password

# IMAP server details for mail.ru
imap_server = "imap.mail.ru"  # Mail.ru IMAP server


def clean(text):
    """Clean text for creating a folder"""
    return "".join(c if c.isalnum() else "_" for c in text)


def download_emails():
    # Connect to the IMAP server
    try:
        imap = imaplib.IMAP4_SSL(imap_server, 993)  # Mail.ru uses port 993 for IMAP [1][2][5]
        imap.login(username, password)
        print("Successfully logged in!")
    except imaplib.IMAP4.error:
        print("Authentication failed. Check your username/password.")
        return

    # Select the mailbox (e.g., "inbox", "sent")
    imap.select("inbox")  # You can change this to "sent" or other folders

    # Search for all emails
    status, messages = imap.search(None, "ALL")
    if status != "OK":
        print("No messages found!")
        return

    message_ids = messages[0].split(b' ')

    for msg_id in message_ids:
        # Fetch the email message by ID
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK":
            print(f"Failed to fetch message {msg_id}")
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        # Decode email headers
        from_value, from_encoding = decode_header(msg.get("From"))[0]
        subject_value, subject_encoding = decode_header(msg.get("Subject"))[0]

        if isinstance(from_value, bytes):
            from_value = from_value.decode(from_encoding or 'utf-8', errors='ignore')
        if isinstance(subject_value, bytes):
            subject_value = subject_value.decode(subject_encoding or 'utf-8', errors='ignore')

        # Create a safe folder name
        sender_name = clean(from_value)
        subject = clean(subject_value)
        folder_name = f"{sender_name}_{subject}"

        # If subject is empty, replace with "No Subject"
        if not subject:
            folder_name = f"{sender_name}_No_Subject"

        # Create the folder
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Save the email content
        email_content = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass  # Not text

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    email_content += body
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    email_content += body

                # Download attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        filepath = os.path.join(folder_name, filename)
                        try:
                            open(filepath, "wb").write(part.get_payload(decode=True))
                            print(f"Downloaded attachment: {filename}")
                        except Exception as e:
                            print(f"Error saving attachment {filename}: {e}")
        else:
            email_content = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        # Save the email body to a text file
        try:
            with open(os.path.join(folder_name, "email_body.txt"), "w", encoding='utf-8') as f:
                f.write(email_content)
        except Exception as e:
            print(f"Error saving email body: {e}")

    # Close the connection
    imap.close()
    imap.logout()


# Before running, ensure IMAP access is enabled in Mail.ru settings
# Also, generate and use a password for external applications if required for enhanced security [3]

# Run the function
download_emails()
