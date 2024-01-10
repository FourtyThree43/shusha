import pyperclip
import re

def extract_links_from_clipboard():
    clipboard_text = pyperclip.paste()
    # print("Clipboard:\n", clipboard_text)
    url_pattern = re.compile(r'https?://\S+')
    urls = url_pattern.findall(clipboard_text)

    return urls

if __name__ == "__main__":
    detected_links = extract_links_from_clipboard()
    if detected_links:
        print("Detected links:")
        for link in detected_links:
            print(link)
    else:
        print("No links found in the clipboard.")
