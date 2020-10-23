__license__ = "Apache 2"
import pickle
import spacy
import pandas as pd
import matplotlib.pyplot as plt

from spacy import displacy
from spacy_lookup import Entity
import helpers

import streamlit as st

bio_fast = pd.read_pickle("data/biology-fast.pkl")
bio_options = []
for row in bio_fast.iterrows():
    bio_options.append((row[1]['Label'], row[1]['URI']))
bio_df = pd.read_pickle("data/biology.pkl")

fast_assignments = []

def _get_state(hash_funcs=None):
    session = helpers._get_session()
    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = helpers._SessionState(session, hash_funcs)
    return session._custom_session_state


@st.cache(allow_output_mutation=True)
def setup_spacy():
    labels = {}
    for row in bio_fast.iterrows():
        uri = row[1]["URI"]
        label = row[1]["Label"]
        labels[uri] = [label,]
    entity = Entity(keywords_dict=labels, label="BIO_FAST")
    nlp = spacy.load("en_core_web_md")
    nlp.add_pipe(entity)
    nlp.remove_pipe("ner")
    return nlp, entity


def header_loading() -> dict:
    state = _get_state()
    st.title("FAST Assignment for Stanford Biology ETDs")
    nlp, entity = setup_spacy()
    if state.druid is None:
        sample = bio_df.sample()
    else:
        sample = bio_df[bio_df['druids'] == state.druid]
    entities = {}
    for i,row in enumerate(sample.iterrows()):
        sample_druid = row[1]['druids']
        state.druid = sample_druid
        st.header(f"{row[1]['title']}")
        st.subheader(f"Druid: {sample_druid}, {row[1]['departments']}")
        st.markdown(f""" Read [PDF](https://purl.stanford.edu/{sample_druid})""")
        doc = nlp(row[1].abstracts)
        st.write(displacy.render(doc, style="ent"), unsafe_allow_html=True)
        entities = {}
        for doc_entity in doc.ents:
            entities[entity.keyword_processor.get_keyword(doc_entity.text)] = doc_entity.text

    state.sync()
    return sample_druid, entities

def left_side(druid_new: str, entities: dict):
    state = _get_state()
    st.sidebar.header(f"Suggested FAST Headings for {druid_new}")
    for fast_uri, label in entities.items():
        if st.sidebar.checkbox(label, key=fast_uri):
            if not fast_uri in fast_assignments:
                fast_assignments.append(fast_uri)
        else:
            if fast_uri in fast_assignments:
                fast_assignments.remove(fast_uri)

    state.sync()

def main():
    state = _get_state()
    message = st.empty()
    sample_druid, entities = header_loading()
    left_side(sample_druid, entities)
    chosen_fast_select = st.sidebar.multiselect("Other FAST Headings", 
                                                bio_options,
                                                format_func=lambda x: x[0])
    if st.sidebar.button(f"Save {sample_druid}"):
        if chosen_fast_select:
            for fast in chosen_fast_select:
                fast_assignments.append(fast[1])
        if helpers.save_fast_to_druid(sample_druid, fast_assignments):
            message.info(f"Successfully Saved FAST subjects for {sample_druid}")
    if st.sidebar.button(f"New Druid"):
        state.druid = None
        state.sync()



if __name__ == '__main__':
    main()
