import streamlit as st
import datetime
import collections

# --- In-memory "databáze" (pro demo) ---
if "users" not in st.session_state:
    st.session_state.users = {
        "michal@firma.cz": "Michal",
        "pavel@firma.cz": "Pavel",
        "jirka@firma.cz": "Jirka",
        "veronika@firma.cz": "Veronika"
    }
if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {
            "id": 1,
            "assigned_to": "michal@firma.cz",
            "shared_with": ["pavel@firma.cz"],
            "description": "Výměna oleje",
            "status": "nový",
            "history": [],
        },
        {
            "id": 2,
            "assigned_to": "pavel@firma.cz",
            "shared_with": [],
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
            # Přidej uživatele do seznamu (pokud ještě není)
            if user_email.strip() not in st.session_state.users:
                st.session_state.users[user_email.strip()] = name.strip() or user_email.strip().split("@")[0].capitalize()
            st.success("Přihlášení OK. Zobrazují se jen vaše úkoly.")
            st.rerun()
    st.stop()

st.write(f"👋 Přihlášen jako **{st.session_state.users.get(st.session_state.user_email, st.session_state.user_email)}** ({st.session_state.user_email})")
if st.button("Odhlásit se"):
    del st.session_state.user_email
    st.rerun()

user_email = st.session_state.user_email
# --- Výpis úkolů pro uživatele (včetně sdílených) ---
my_tasks = [t for t in st.session_state.tasks if t["assigned_to"] == user_email or user_email in t.get("shared_with", [])]

st.subheader("Moje úkoly")

if not my_tasks:
    st.info("Nemáte zatím žádné úkoly.")
else:
    # Zjisti, zda má uživatel nějaký rozjetý úkol (spusten)
    any_running = any(t['status'] == "spusten" for t in my_tasks)
    for task in my_tasks:
        st.markdown(f"### {task['description']}")
        st.write(f"**Stav:** {task['status'].upper()}")
        # Kdo má úkol sdílený
        assigned = st.session_state.users.get(task["assigned_to"], task["assigned_to"])
        shared_with_names = [st.session_state.users.get(u, u) for u in task.get("shared_with", [])]
        st.write(f"**Přiřazeno:** {assigned}")
        if shared_with_names:
            st.write("**Sdíleno s:** " + ", ".join(shared_with_names))
        # Akce k úkolu
        cols = st.columns(5)
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
                if action == "Spustit" and any_running and task['status'] != "spusten":
                    cols[i].button("Spustit", key=f"{task['id']}_{action}", disabled=True)
                    cols[i].markdown(
                        "<span style='color:red;font-size:12px'>Nejprve přerušte nebo dokončete rozjetý úkol.</span>",
                        unsafe_allow_html=True)
                else:
                    if cols[i].button(action, key=f"{task['id']}_{action}"):
                        action_clicked = action
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if action_clicked:
            # Při spuštění úkolu automaticky přeruš ostatní rozjeté
            if action_clicked == "Spustit":
                for t in my_tasks:
                    if t['status'] == "spusten" and t['id'] != task['id']:
                        t['status'] = "prerusen"
                        t['history'].append({
                            "action": "pause",
                            "note": f"automaticky přerušeno při spuštění úkolu: {task['description']}",
                            "timestamp": now,
                            "user": user_email,
                        })
                task['status'] = "spusten"
                act = "start"
                note = ""
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
                note = ""
            elif action_clicked == "Dokončit":
                task['status'] = "hotovo"
                act = "stop"
                note = ""
            else:
                act = ""
                note = ""
            # Zaznamenat historii
            if act:
                task['history'].append({
                    "action": act,
                    "note": note,
                    "timestamp": now,
                    "user": user_email,
                })
            st.success(f"Akce {action_clicked} uložena.")
            st.rerun()

        # --- Sdílení úkolu s kolegy (pouze vlastník úkolu = assigned_to) ---
        if user_email == task["assigned_to"]:
            with st.expander("Sdílet úkol s kolegy / požádat o pomoc"):
                # Vyber kolegy (více najednou, kromě sebe a už přiřazených)
                potential_helpers = [email for email in st.session_state.users.keys()
                                     if email != task["assigned_to"]
                                     and email not in task.get("shared_with",[])]
                selected = st.multiselect(
                    f"Vyber kolegy, kterým úkol sdílet (pro úkol {task['id']}):",
                    options=potential_helpers,
                    format_func=lambda x: st.session_state.users.get(x, x)
                )
                if st.button("Sdílet s vybranými kolegy", key=f"sharebtn_{task['id']}"):
                    if "shared_with" not in task:
                        task["shared_with"] = []
                    added = []
                    for email in selected:
                        if email not in task["shared_with"]:
                            task["shared_with"].append(email)
                            added.append(st.session_state.users.get(email, email))
                    if added:
                        st.success("Úkol nyní sdílen s: " + ", ".join(added))
                        st.rerun()
                    else:
                        st.info("Nebyl vybrán žádný nový kolega nebo již byl úkol sdílen.")

        # --- Historie a přehled práce ---
        with st.expander("Historie práce na úkolu"):
            if not task['history']:
                st.write("Zatím žádná aktivita.")
            else:
                for h in task['history']:
                    st.write(f"{h['timestamp']}: **{h['action']}** {st.session_state.users.get(h['user'], h['user'])} {('(' + h['note'] + ')' ) if h['note'] else ''}")
                # Výpočet času jednotlivých lidí
                st.write("---")
                st.write("🕑 Přehled práce jednotlivých lidí:")
                times = collections.defaultdict(float)
                last_start = {}
                for h in task['history']:
                    user = h["user"]
                    t = datetime.datetime.strptime(h["timestamp"], "%Y-%m-%d %H:%M:%S")
                    if h["action"] in ("start", "resume"):
                        last_start[user] = t
                    elif h["action"] in ("pause", "stop"):
                        if user in last_start:
                            times[user] += (t - last_start[user]).total_seconds() / 60
                            last_start.pop(user)
                for user, mins in times.items():
                    st.write(f"- {st.session_state.users.get(user,user)}: {mins:.1f} minut")

# --- ADMIN: Přidání úkolu ---
with st.expander("Správa úkolů (admin)"):
    st.write("Přidej nový úkol pro někoho:")
    with st.form("add_task_form"):
        email = st.selectbox("Vyber mechanika", options=list(st.session_state.users.keys()))
        desc = st.text_input("Popis úkolu", value="Servis brzd")
        add_task_btn = st.form_submit_button("Přidat úkol")
        if add_task_btn and email and desc:
            st.session_state.tasks.append({
                "id": max([t["id"] for t in st.session_state.tasks]+[0]) + 1,
                "assigned_to": email.strip(),
                "shared_with": [],
                "description": desc.strip(),
                "status": "nový",
                "history": [],
            })
            st.success("Úkol přidán.")
            st.rerun()
