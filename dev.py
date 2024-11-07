import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt  # Importing matplotlib for plotting

# Google Sheets API setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('stock-management-441000-b09dc6a7c5cd.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Stock-Records").sheet1  # Replace with your Google Sheet name

# Function to fetch data from Google Sheets
def fetch_data():
    records = sheet.get_all_records()
    return pd.DataFrame(records)

# Function to calculate balances
def calculate_balances(df):
    balance_dict = {}
    for _, row in df.iterrows():
        product = row['PRODUCT']
        transaction_type = row['TYPE']
        quantity = row['QUANTITY']

        if product not in balance_dict:
            balance_dict[product] = 0

        if transaction_type == "In":
            balance_dict[product] += quantity
        elif transaction_type == "Out":
            balance_dict[product] -= quantity
        elif transaction_type == "Adjustment":
            balance_dict[product] += quantity

    return balance_dict

# Function to update the balance in Google Sheets
def update_balance_in_sheet(balance_dict):
    # Get all product names from the sheet
    product_names = sheet.col_values(2)[1:]  # Assuming product names are in the 2nd column starting from the 2nd row
    for i, product in enumerate(product_names):
        if product in balance_dict:
            sheet.update_cell(i + 2, 6, balance_dict[product])  # Update balance in the 6th column

# Function to send email notification
def send_email(subject1, body1):
    sender_email = "vardhanv759@gmail.com"
    receiver_email = "Parsalidos@gmail.com"
    password = "durf bnas acqs orud"

    # Email structure
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject1
    msg.attach(MIMEText(body1, "plain"))

    # Sending the email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")

# Page setup
st.set_page_config(page_title="Stock Management", layout="centered")

# Sidebar Navigation
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to", ["Submit New Record", "History of Submissions", "Product Balance", "Data Analytics"])

if menu == "Submit New Record":
    st.image("lidos.png", use_column_width=True)
    st.header("Stock Management System")
    st.subheader("Submit New Record")

    # List of all products
    products = [
        '', "Stain remover", "Room fragrance", "Laundry Powder", "Glade airfreshner", "Spray and Wipe",
        "Furniture Polish", "Rubbish bags", "Window cleaner", "Hoover bags", "Gloves", "Mould cleaner",
        "Toilet paper", "Fairy", "Bin liner", "Coconut shampoo", "Duster", "5 litre pump",
        "Microfibre Glass", "Microfibre Cloth Blue", "Sanitizer", "Viakal", "One shot drain",
        "Toilet Brush", "Mould Dettol", "Bottle green complete", "Telephone sanitiser", "Selactive",
        "Selguard", "De-scalar", "Sanitary bags", "Bathroom cleaner spray", "Glade airfreshner Solid",
        "Scourer", "Bottle Blue", "Perfume", "Toilet renovator", "Sponge", "Pump Tap",
        "Chewing gum", "Professional floor cleaner", "Glaze", "Glalid Solid", "Carpet Shake & Vac",
        "Flash Bleach", "Other"
    ]

    # Set up input fields
    product_name = st.selectbox("Select Product", products)
    if product_name == 'Other':
        product_name = st.text_area('Product Name')
    transaction_type = st.radio("Select Transaction Type", ["In", "Out", "Adjustment"])
    quantity = st.slider("Enter Quantity", min_value=0, max_value=10)
    comments = st.text_area("Comments (optional)")

    # Submit button
    if st.button("Submit"):
        # Current timestamp
        current_date = datetime.now().strftime('%d-%m-%Y')

        # Prepare data for saving
        data = [current_date, product_name, transaction_type, quantity, comments]

        # Append the data to Google Sheets
        sheet.append_row(data)

        # Update balances
        df = fetch_data()
        balances = calculate_balances(df)


        # Confirmation message
        st.success(f"Record for {product_name} has been saved successfully!")
        update_balance_in_sheet(balances)

# 1. History of Submissions
elif menu == "History of Submissions":
    st.subheader("📜 History of Submissions")

    # Fetch data
    df = fetch_data()

    # Date range picker
    start_date = st.date_input("Start Date", value=pd.to_datetime("2024-11-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-11-30"))

    # Filter data based on date range
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y')
        filtered_df = df[(df['DATE'] >= pd.to_datetime(start_date)) & (df['DATE'] <= pd.to_datetime(end_date))]
        if st.button('Search'):
            st.dataframe(filtered_df)
    else:
        st.write("No date column found in the data.")

# 2. Product Balance
elif menu == "Product Balance":
    st.subheader("📦 Product Balance")

    # Fetch data
    df = fetch_data()

    # Calculate the balance for each product
    if not df.empty:
        balances = calculate_balances(df)
        balance_df = pd.DataFrame(list(balances.items()), columns=['PRODUCT', 'BALANCE'])
        st.dataframe(balance_df)

        # Check for low balance
        low_balance_products = balance_df[balance_df['BALANCE'] <= 2]
        if not low_balance_products.empty:
            email_body = "The following products have a stock balance of less than 2 units:\n\n"
            for index, row in low_balance_products.iterrows():
                email_body += f"{row['PRODUCT']}: {row['BALANCE']}\n"
            # Add a button to trigger the low balance alert
            if st.button("Send Low Balance Alert"):
                send_email("Low Stock Alert", email_body)
                st.success("Low balance alert sent successfully!")
        else:
            st.info("No products have a balance less than 2 units.")  # Display a message if no low balance is found
    else:
        st.write("No data available for product balance.")

# 3. Data Analytics
elif menu == "Data Analytics":
    st.subheader("📊 Data Analytics")

    # Fetch data
    df = fetch_data()

    # Example analytics: product usage trend
    if not df.empty:
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y')
        df['Month'] = df['DATE'].dt.strftime('%B %Y')
        product_trend = df.groupby(['PRODUCT', 'Month']).size().unstack(fill_value=0)
        st.bar_chart(product_trend)

        # Aggregate data for "In", "Out", and "Adjustment" for each product
        product_in = df[df['TYPE'] == 'In'].groupby('PRODUCT')['QUANTITY'].sum()
        product_out = df[df['TYPE'] == 'Out'].groupby('PRODUCT')['QUANTITY'].sum()
        product_adjustment = df[df['TYPE'] == 'Adjustment'].groupby('PRODUCT')['QUANTITY'].sum()

        # Plotting the product balances using matplotlib
        balances = calculate_balances(df)
        balance_df = pd.DataFrame(list(balances.items()), columns=['PRODUCT', 'BALANCE'])
        st.subheader("📊 Product Balances")
        fig, ax = plt.subplots()
        balance_df.set_index('PRODUCT')['BALANCE'].plot(kind='bar', ax=ax, color= 'black')
        ax.set_title("Product Balances")
        ax.set_xlabel("Product")
        ax.set_ylabel("Balance")
        plt.xticks(rotation=45)
        st.pyplot(fig)  # Display the bar chart

        # Plotting the "In" quantities
        st.subheader("📈 In Quantities by Product")
        fig_in, ax_in = plt.subplots()
        product_in.plot(kind='bar', ax=ax_in)
        ax_in.set_title("In Quantities by Product")
        ax_in.set_xlabel("Product")
        ax_in.set_ylabel("Quantity")
        plt.xticks(rotation=45)
        st.pyplot(fig_in)

        # Plotting the "Out" quantities
        st.subheader("📉 Out Quantities by Product")
        fig_out, ax_out = plt.subplots()
        product_out.plot(kind='bar', ax=ax_out, color='red')
        ax_out.set_title("Out Quantities by Product")
        ax_out.set_xlabel("Product")
        ax_out.set_ylabel("Quantity")
        plt.xticks(rotation=45)
        st.pyplot(fig_out)

        # Plotting the "Adjustment" quantities
        st.subheader("🔧 Adjustment Quantities by Product")
        fig_adjustment, ax_adjustment = plt.subplots()
        product_adjustment.plot(kind='bar', ax=ax_adjustment, color='orange')
        ax_adjustment.set_title("Adjustment Quantities by Product")
        ax_adjustment.set_xlabel("Product")
        ax_adjustment.set_ylabel("Quantity")
        plt.xticks(rotation=45)
        st.pyplot(fig_adjustment)
    else:
        st.write("No data available for analytics.")