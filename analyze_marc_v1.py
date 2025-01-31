import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup as soup
import lxml.etree as ET
import unicodedata
import os
import io

from lxml.html.defs import event_attrs
from pandas.core.dtypes.generic import create_pandas_abc_type

#--------------------------- SETUP ----------------------
# set default layout:
st.set_page_config(layout="wide")
with st.sidebar:
    st.write("Hello my friend!")
    st.write("You found the most amazing tool for MARC21-analysis. Enjoy!")

# load field mapping as dataframe:
#dir_path = os.path.dirname(os.path.realpath(__file__))
#data = dir_path +"/field_mapping.csv"
df = pd.read_csv(field_mapping.csv, encoding="utf-8")
st.dataframe(df)



# --------------------- ALL FUNCTIONS -------------------

## define all functions:
def parse_record(record, marc21):

    ns = {"marc": "http://www.loc.gov/MARC21/slim"}
    record = ET.fromstring(unicodedata.normalize("NFC", str(record)))

    def extract_text(xpath_query, record):
        fields = record.xpath(xpath_query, namespaces=ns)
        if fields:
            return "; ".join(field.text.replace('\x98', '').replace('\x9c', '') for field in fields if field.text)
        return "unknown"

    meta_dict = {}
    for key, value in marc21.items():
        extracted_value = extract_text(value, record)
        meta_dict[key] = extracted_value

    return meta_dict

@st.cache_resource
def parse_xml(content):
    # Parse XML content using BeautifulSoup and lxml
    xml = soup(content, features='xml')
    records = xml.find_all('record', {'type': 'Bibliographic'})
    st.success(f"Anzahl Datensätze: {len(records)}", icon="✅")
    return records
    pass

@st.cache_data
def extract_values(df, fields):
    result = {}
    result["idn"] = "marc:controlfield[@tag='001']" #add idn as first no matter what
    for field in fields:
        matching_row = df[df['name'] == field]
        if not matching_row.empty:
            result[field] = matching_row['marc_field'].values[0]
    return result
    #return df[df['name'].isin(fields)].set_index('name')['marc_field'].to_dict()


@st.fragment
def read_file():
    file = st.file_uploader("Choose an xml-file")
    if file is not None and file.name.endswith(".xml"):
        content = file.read()
        records = parse_xml(content)
        if records:
            return records
        else:
            st.write("Keine gültigen Datensätze gefunden.")
    elif file is not None:
        st.write("Ungültiges Dateiformat. Bitte wählen Sie eine .xml-Datei aus.")


@st.fragment
def get_fields(fields, expert):
    if expert == None:
        marc21 = extract_values(df, fields)
    else:
        st.write("Sorry, the expert mode is not ready yet and your custom field will not be displayed. "
                 "Please try again later.")
        marc21 = extract_values(df, fields)
    return marc21



#------------------------------------------FRONTEND -----------------------------------------------------------------

st.title("Marc21 Analyse-Tool")
st.write("lorem ipsum bla bli blubb")

main, right = st.columns([0.8, 0.2], vertical_alignment="center")

with main:

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.write("Bitte wählen Sie hier die Informationen, die Sie aus den Datensätzen übernehmen möchten:")
        fields = st.pills(
            "Klicken Sie alle Felder an, die Sie übernehmen möchten. Die gewählte Reihenfolge wird für die Ausgabe berücksichtigt:",
            ["Creator", "Creator-rela", "Title", "Subtitle", "Statement of responsibility", "Publisher",
             "Place of Publication",
             "Year of Publication", "Pages", "Note", "Thesis statement", "Added creator", "Added creator-rela"],
            selection_mode="multi"
        )
        expert = st.checkbox("Expertenmodus")
        if expert:
            expert_field = st.text_input("Bitte neues Feld in der Form 'Name' (frei wählbar), 'Nummer des Datafields', 'Buchstabe "
                                         "des Subfields' eingeben.", "ISBN, 020, a")
            marc21 = get_fields(fields, expert_field)
        else:
            marc21 = get_fields(fields, None)

    with col2:
        records = read_file()

    if marc21 and st.button("Let's go!", type="primary"):
        if not records:
            st.warning("Please upload an xml-file first!")
        else:

            progress_bar = st.progress(0)
            status_text = st.empty()

            result = []
            for i, record in enumerate(records):
                result.append(parse_record(record, marc21))
                progress = (i + 1) / len(records)
                progress_bar.progress(progress)
                status_text.text(f"Verarbeite Datensatz {i + 1} von {len(records)}")

            df_result = pd.DataFrame(result)
            status_text.text("Verarbeitung abgeschlossen!")

            with st.expander("Vorschau des Ergebnisses"):
                st.dataframe(df_result)


            def convert_to_csv(df_result):
                return df_result.to_csv().encode('utf-8')


            def convert_to_xlsx(df_result):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_result.to_excel(writer, index=False)
                output.seek(0)
                return output.getvalue()


            button1, button2 = st.columns([0.2, 0.8])
            with button1:
                @st.fragment
                def save_as_csv():
                    st.download_button(
                        label="Download data as CSV",
                        data=convert_to_csv(df_result),
                        file_name="result.csv",
                        mime="text/csv",
                    )
                save_as_csv()

            with button2:
                @st.fragment
                def save_as_excel():
                    st.download_button(
                        label="Download data as Excel",
                        data=convert_to_xlsx(df_result),
                        file_name="result.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                save_as_excel()

with right:
    st.write()

st.write("")
st.write("")
with st.expander("Design Möglichkeiten"):

    tab1, tab2 = st.tabs(["Checkbox", "Mulitselect"])

    with tab1:
        st.subheader("For design-purposes only: Checkbox")
        creator = st.checkbox("Creator (100$a)")
        creator_rela = st.checkbox("Creator-rela (100$e)")
        title = st.checkbox("Title (245$a)")
        subtitle = st.checkbox("Subtitle (245$b)")
        responsibility = st.checkbox("Statementent of responsibility (245$c)")
        publisher = st.checkbox("Publisher (264$a)")
        place = st.checkbox("Place of publication (264$b)")
        st.write("...")
    with tab2:
        st.subheader("For design-purposes only: Multiselect")
        fields = st.multiselect(
            "Klicken Sie alle Felder an, die Sie übernehmen möchten. Die gewählte Reihenfolge wird für die Ausgabe berücksichtigt:",
            ["Creator", "Creator-rela", "Title", "Subtitle", "Statement of responsibility", "Publisher",
             "Place of Publication",
             "Year of Publication", "Pages", "Note", "Thesis statement", "Added creator", "Added creator-rela"],
            []
        )
