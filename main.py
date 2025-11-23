import requests
from telegram.ext import Updater, CommandHandler
from datetime import datetime, timedelta

# Put your SheetDB API URL here
SHEETDB_API_URL = "https://sheetdb.io/api/v1/pjgu50vbdx94v"
# Put your Telegram Bot token here
TELEGRAM_TOKEN = "8336104664:AAHYJe0GtUnwcPdQ0wFCzba3N76VoLvDeOw"

def fetch_sheet():
    r = requests.get(SHEETDB_API_URL)
    r.raise_for_status()  # Raise error if bad response
    return r.json()

def summary(update, context):
    data = fetch_sheet()
    # Rows 15 to 19 correspond to zero-based index 14 to 18 in data list
    indices = [14, 15, 16, 17, 18]
    metrics = [data[i]['Member Name'] for i in indices]
    values = [data[i]['JOINING FEES'] for i in indices]
    message = "\n".join(f"{m}: {v}" for m, v in zip(metrics, values))
    update.message.reply_text(message)

def week(update, context):
    data = fetch_sheet()
    today = datetime.now()
    weekday = today.weekday()  # Monday=0 ... Sunday=6
    # Calculate last Saturday (weekday 5)
    days_since_sat = (weekday - 5) % 7 or 7
    last_saturday = today - timedelta(days=days_since_sat)
    # Format date for matching spreadsheet column header "dd MMM" e.g., "13 Sep"
    col_date_str = last_saturday.strftime("%d %b")
    keys = list(data[0].keys())
    target_col = None
    for col in keys:
        if col_date_str in col:
            target_col = col
            break
    if not target_col:
        update.message.reply_text("Cannot find payments for last Saturday.")
        return
    message_lines = [f"Hey, the payment of date({last_saturday.strftime('%d-%m-%Y')}) was recorded as:"]
    # Rows 2 to 11 (index 1 to 10) contain members
    for row in data[1:11]:
        name = row['Member Name']
        paid = row.get(target_col, "0")
        message_lines.append(f"{name} {paid}")
    update.message.reply_text("\n".join(message_lines))

def advance(update, context):
    data = fetch_sheet()
    keys = list(data[0].keys())[2:-1]  # Columns with dates, skipping first 2 and last
    today = datetime.now()
    advances = []
    for row in data[1:11]:
        # Check from right to left for future payment dates
        for col in reversed(keys):
            val = row.get(col, "").strip()
            if val and val != "0":
                try:
                    pay_date = datetime.strptime(col, "%d %b")
                    pay_date = pay_date.replace(year=today.year)
                    if pay_date > today:
                        advances.append(f"{row['Member Name']} paid up to {col}")
                except:
                    continue
                break
    if advances:
        update.message.reply_text("Hey the following advances can be seen in my records:\n" + "\n".join(advances))
    else:
        update.message.reply_text("No advances found.")

def dues(update, context):
    data = fetch_sheet()
    keys = list(data[0].keys())[2:-1]
    today = datetime.now()
    dues_list = []
    for row in data[1:11]:
        for col in keys:
            try:
                col_date = datetime.strptime(col, "%d %b").replace(year=today.year)
                if col_date > today:
                    break  # Stop checking future dates for dues
                paid = row.get(col, "").strip()
                if not paid or paid == "0":
                    dues_list.append(f"{row['Member Name']} dues in {col}")
            except:
                continue
    if dues_list:
        update.message.reply_text("Members with dues:\n" + "\n".join(dues_list))
    else:
        update.message.reply_text("No dues found up to today.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('summary', summary))
    dp.add_handler(CommandHandler('week', week))
    dp.add_handler(CommandHandler('advance', advance))
    dp.add_handler(CommandHandler('dues', dues))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
