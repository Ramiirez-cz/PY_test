import streamlit as st
import datetime

# --- In-memory "databáze" (pro demo) ---
if "users" not in st.session_state:
    st.session_state.users = {}
if "tasks" not in st.session_state:
    # Ukázkové úkoly pro 2 uživatele
    st.session_state.tasks = [
        {
            "id": 1,
            "assigned_to": "michal@firma.cz",
            "description": "Výměna oleje",
            "status": "nový",
            "history": [],
        },
        {
            "id": 2,
            "assigned_to": "pavel@firma.cz",
            "description": "Diagnostika motoru",
            "status": "nový",
            "history": [],
        }
    ]

# --- Přihlášení ---
st.title("Mechanik – sledování úkolů (web demo)")
if "user_email" not in st.session_state:
    with st.form("login_form"):
        st.write("Přihlášení")
        user_email = st.text_input("E-mail")
        name = st.text_input("Jméno")
        submitted = st.form_submit_button("Přihlásit se")
        if submitted and user_email:
            st.session_state.user_email = user_email.strip()
            st.session_state.name = name.strip()
            st.success("Přihlášení OK. Zobrazují se jen vaše úkoly.")
            st.rerun()
    st.stop()

st.write(f"👋 Přihlášen jako **{st.session_state.user_email}**")
if st.button("Odhlásit se"):
    del st.session_state.user_email
    st.rerun()

# --- Výpis úkolů pro uživatele ---
user_email = st.session_state.user_email
my_tasks = [t for t in st.session_state.tasks if t["assigned_to"] == user_email]
st.subheader("Moje úkoly")

if not my_tasks:
    st.info("Nemáte zatím žádné úkoly.")
else:
    for task in my_tasks:
        st.markdown(f"### {task['description']}")
        st.write(f"**Stav:** {task['status'].upper()}")
        # Akce k úkolu
        cols = st.columns(5)
        # Definuj, které akce mají být povolené podle stavu:
        allowed = {
            "nový": ["Spustit"],
            "spusten": ["Přerušit (oběd)", "Přerušit (pomoc)", "Dokončit"],
            "prerusen": ["Pokračovat", "Dokončit"],
            "hotovo": []
        }
        actions = allowed.get(task['status'], [])
        action_clicked = None
        for i, action in enumerate(["Spustit", "Přerušit (oběd)", "Přerušit (pomoc)", "Pokračovat", "Dokončit"]):
            if action in actions:
                if cols[i].button(action, key=f"{task['id']}_{action}"):
                    action_clicked = action
        if action_clicked:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            note = ""
            if action_clicked == "Spustit":
                task['status'] = "spusten"
                act = "start"
            elif action_clicked == "Přerušit (oběd)":
                task['status'] = "prerusen"
                act = "pause"
                note = "oběd"
            elif action_clicked == "Přerušit (pomoc)":
                task['status'] = "prerusen"
                act = "pause"
                note = "pomoc na jiném úkolu"
            elif action_clicked == "Pokračovat":
                task['status'] = "spusten"
                act = "resume"
            elif action_clicked == "Dokončit":
                task['status'] = "hotovo"
                act = "stop"
            else:
                act = ""
            # Zaznamenat historii
            task['history'].append({
                "action": act,
                "note": note,
                "timestamp": now,
                "user": user_email,
            })
            st.success(f"Akce {action_clicked} uložena.")
            st.rerun()

        # Zobraz historii u úkolu
        with st.expander("Historie práce na úkolu"):
            if not task['history']:
                st.write("Zatím žádná aktivita.")
            else:
                for h in task['history']:
                    st.write(f"{h['timestamp']}: **{h['action']}** {('(' + h['note'] + ')' ) if h['note'] else ''}")

# --- ADMIN: Přidání úkolu ---
with st.expander("Správa úkolů (admin)"):
    st.write("Přidej nový úkol pro někoho:")
    with st.form("add_task_form"):
        email = st.text_input("E-mail mechanika", value="michal@firma.cz")
        desc = st.text_input("Popis úkolu", value="Servis brzd")
        add_task_btn = st.form_submit_button("Přidat úkol")
        if add_task_btn and email and desc:
            st.session_state.tasks.append({
                "id": max([t["id"] for t in st.session_state.tasks]+[0]) + 1,
                "assigned_to": email.strip(),
                "description": desc.strip(),
                "status": "nový",
                "history": [],
            })
            st.success("Úkol přidán.")
            st.rerun()
