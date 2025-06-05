
import json
import os
import datetime
import random  # Pour des suggestions initiales et des simulations simples

class INSFLocalLearner:
    _PROFILES_DIR = "user_profiles"

    def __init__(self):
        self._users_data = {}
        if not os.path.exists(self._PROFILES_DIR):
            os.makedirs(self._PROFILES_DIR)
        self._load_all_profiles()

    def _get_profile_path(self, user_id: str) -> str:
        return os.path.join(self._PROFILES_DIR, f"{user_id}_profile.json")

    def _load_all_profiles(self):
        for filename in os.listdir(self._PROFILES_DIR):
            if filename.endswith("_profile.json"):
                user_id = filename.replace("_profile.json", "")
                try:
                    with open(self._get_profile_path(user_id), 'r', encoding='utf-8') as f:
                        self._users_data[user_id] = json.load(f)
                except Exception as e:
                    print(f"Erreur lors du chargement du profil {user_id}: {e}")

    def _save_user_profile(self, user_id: str):
        if user_id not in self._users_data:
            print(f"Profil utilisateur {user_id} non trouvé en mémoire.")
            return
        profile_path = self._get_profile_path(user_id)
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(self._users_data[user_id], f, indent=4)
        except IOError as e:
            print(f"Erreur lors de la sauvegarde du profil {user_id}: {e}")

    def create_or_load_user_profile(self, user_id: str) -> dict:
        if user_id in self._users_data:
            return self._users_data[user_id]

        profile_path = self._get_profile_path(user_id)
        if os.path.exists(profile_path):
            try:
                with open(profile_path, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                    self._users_data[user_id] = profile
                    return profile
            except Exception:
                pass

        default_profile = {
            "user_id": user_id,
            "trust_score": 70,
            "speech_speed_avg": 150.0,
            "preferred_voice": "Sol",
            "feedback_history": [],
            "last_emotion": "neutre",
            "comprehension_scores": [],
            "dropout_risk_score": 0.1,
            "creation_date": datetime.datetime.now().isoformat(),
            "last_update_date": datetime.datetime.now().isoformat()
        }
        self._users_data[user_id] = default_profile
        self._save_user_profile(user_id)
        return default_profile

    def record_interaction(self, user_id: str, voice_id: str, feedback: str, emotion: str, speech_speed_sample: float = None):
        if user_id not in self._users_data:
            return
        profile = self._users_data[user_id]
        interaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "voice_id": voice_id,
            "feedback": feedback,
            "emotion": emotion,
            "speech_speed_sample": speech_speed_sample
        }
        profile["feedback_history"].append(interaction)
        profile["last_emotion"] = emotion
        profile["last_update_date"] = datetime.datetime.now().isoformat()
        if feedback.lower() in ["positif", "clair", "excellent", "oui"]:
            profile["trust_score"] = min(100, profile["trust_score"] + 2)
        elif feedback.lower() in ["négatif", "confus", "mauvais", "non"]:
            profile["trust_score"] = max(0, profile["trust_score"] - 5)
        if speech_speed_sample is not None:
            n_samples = len([inter for inter in profile["feedback_history"] if inter.get("speech_speed_sample") is not None])
            if n_samples > 1:
                profile["speech_speed_avg"] = ((profile["speech_speed_avg"] * (n_samples - 1)) + speech_speed_sample) / n_samples
            else:
                profile["speech_speed_avg"] = speech_speed_sample
        self._save_user_profile(user_id)

    def calculate_comprehension_score(self, text: str, expected_keywords: list[str]) -> float:
        if not text or not expected_keywords:
            return 0.0
        text_lower = text.lower()
        found_keywords = sum(1 for kw in expected_keywords if kw.lower() in text_lower)
        return found_keywords / len(expected_keywords)

    def add_comprehension_score_to_profile(self, user_id: str, score: float):
        if user_id not in self._users_data:
            return
        profile = self._users_data[user_id]
        profile["comprehension_scores"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "score": score
        })
        if score < 0.3 and profile["trust_score"] > 10:
            profile["trust_score"] = max(0, profile["trust_score"] - 3)
        elif score > 0.7 and profile["trust_score"] < 95:
            profile["trust_score"] = min(100, profile["trust_score"] + 1)
        profile["last_update_date"] = datetime.datetime.now().isoformat()
        self._save_user_profile(user_id)

    def suggest_voice_adjustment(self, user_id: str) -> dict:
        if user_id not in self._users_data:
            return None
        profile = self._users_data[user_id]
        suggestion = {"current_voice": profile["preferred_voice"], "suggestion": None, "reason": ""}
        recent_feedbacks = profile["feedback_history"][-5:]
        neg_feedbacks = [fb for fb in recent_feedbacks if fb["voice_id"] == profile["preferred_voice"] and fb["feedback"].lower() in ["négatif", "confus", "lent", "rapide"]]
        if profile["trust_score"] < 50 and len(neg_feedbacks) >= 2:
            choices = [v for v in ["A", "B", "C", "D", "E"] if v != profile["preferred_voice"]]
            if choices:
                suggestion["suggestion"] = random.choice(choices)
                suggestion["reason"] = f"Score de confiance faible et {len(neg_feedbacks)} feedbacks négatifs."
        return suggestion

    def analyze_dropout_risk(self, user_id: str) -> float:
        if user_id not in self._users_data:
            return 0.9
        profile = self._users_data[user_id]
        risk_score = profile.get("dropout_risk_score", 0.1)
        if profile["trust_score"] < 30:
            risk_score += 0.3
        elif profile["trust_score"] < 50:
            risk_score += 0.15
        num_interactions = len(profile["feedback_history"])
        if num_interactions < 3:
            risk_score += 0.2
        else:
            if profile["feedback_history"]:
                last_date = datetime.datetime.fromisoformat(profile["feedback_history"][-1]["timestamp"])
                days_inactive = (datetime.datetime.now() - last_date).days
                if days_inactive > 14:
                    risk_score += 0.25
                elif days_inactive > 7:
                    risk_score += 0.1
        neg_feedbacks = sum(1 for fb in profile["feedback_history"] if fb["feedback"].lower() in ["négatif", "confus", "mauvais"])
        if num_interactions > 0:
            neg_ratio = neg_feedbacks / num_interactions
            if neg_ratio > 0.6:
                risk_score += 0.3
            elif neg_ratio > 0.4:
                risk_score += 0.15
        if profile["comprehension_scores"]:
            avg_comp = sum(cs["score"] for cs in profile["comprehension_scores"]) / len(profile["comprehension_scores"])
            if avg_comp < 0.4 and len(profile["comprehension_scores"]) > 3:
                risk_score += 0.2
        profile["dropout_risk_score"] = min(max(risk_score, 0.0), 1.0)
        profile["last_update_date"] = datetime.datetime.now().isoformat()
        self._save_user_profile(user_id)
        return profile["dropout_risk_score"]

    def load_knowledge_base(self, path: str = "insf_knowledge_base.json") -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur de chargement de la base de connaissances: {e}")
            return {}

    def analyze_text_context(self, user_input: str, knowledge: dict) -> dict:
        context = {}
        user_text = user_input.lower()
        for category, keywords in knowledge.items():
            found = [kw for kw in keywords if kw.lower() in user_text]
            if found:
                context[category] = found
        return context

if __name__ == "__main__":
    learner = INSFLocalLearner()
    print("=== TEST DU MOTEUR INSF ===")

    # Création de profils
    user1 = "test_utilisateur_001"
    profile = learner.create_or_load_user_profile(user1)
    print("Profil créé :", profile)

    # Interaction simulée
    learner.record_interaction(user1, "A", "positif", "joyeux", 160.0)
    learner.record_interaction(user1, "A", "confus", "triste", 150.0)

    # Score de compréhension
    sample_text = "Je pense que c'est un dossier médical et confidentiel"
    expected = ["médical", "confidentiel", "fichier"]
    score = learner.calculate_comprehension_score(sample_text, expected)
    learner.add_comprehension_score_to_profile(user1, score)
    print(f"Score compréhension : {score:.2f}")

    # Suggestion de voix
    suggestion = learner.suggest_voice_adjustment(user1)
    print("Suggestion de voix :", suggestion)

    # Analyse de contexte avec base
    kb = learner.load_knowledge_base()
    context = learner.analyze_text_context(sample_text, kb)
    print("Contexte détecté :", context)

    # Risque d'abandon
    risk = learner.analyze_dropout_risk(user1)
    print(f"Risque d'abandon : {risk:.2f}")

    def update_emotion_timeline(self, user_id: str, emotion: str):
        if user_id not in self._users_data:
            return
        emotion_log_path = os.path.join(self._PROFILES_DIR, f"{user_id}_emotion_log.json")
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "emotion": emotion
        }
        log = []
        if os.path.exists(emotion_log_path):
            try:
                with open(emotion_log_path, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception:
                pass
        log.append(entry)
        with open(emotion_log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4)

    def detect_emotion_trend(self, user_id: str, window: int = 5) -> str:
        emotion_log_path = os.path.join(self._PROFILES_DIR, f"{user_id}_emotion_log.json")
        if not os.path.exists(emotion_log_path):
            return "Aucune tendance détectée."
        try:
            with open(emotion_log_path, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            return "Erreur de lecture du journal émotionnel."
        recent = log[-window:]
        emotions = [e["emotion"] for e in recent]
        if emotions.count("triste") >= 3:
            return "Tu sembles souvent triste dernièrement. Est-ce que je peux t’accompagner davantage ?"
        elif emotions.count("joyeux") >= 3:
            return "Je remarque beaucoup de joie ces derniers temps, ça me fait plaisir !"
        elif len(set(emotions)) == 1:
            return f"Tu sembles plutôt stable émotionnellement ({emotions[0]})."
        return "Tes émotions ont été assez variées récemment. Je reste attentive."

    def analyze_user_rhythm(self, user_id: str, threshold_days: int = 3) -> str:
        if user_id not in self._users_data:
            return "Utilisateur non trouvé."

        profile = self._users_data[user_id]
        if not profile["feedback_history"]:
            return "Je n’ai pas encore assez d’interactions pour analyser ton rythme."

        try:
            last_interaction_date = datetime.datetime.fromisoformat(profile["feedback_history"][-1]["timestamp"])
            days_since_last = (datetime.datetime.now() - last_interaction_date).days

            if days_since_last > threshold_days:
                return f"Tu n’étais pas venu me parler depuis {days_since_last} jours. Est-ce que tout va bien ?"
            elif days_since_last == 0:
                return "Merci de revenir me voir aujourd’hui !"
            else:
                return f"On s’est reparlé il y a {days_since_last} jours. Ravi de te retrouver."
        except Exception:
            return "Erreur dans le suivi du rythme d’interaction."

    def suggest_adaptive_voice(self, user_id: str) -> str:
        if user_id not in self._users_data:
            return "Utilisateur non trouvé."

        profile = self._users_data[user_id]
        last_emotion = profile.get("last_emotion", "neutre").lower()
        hour = datetime.datetime.now().hour

        # Base sur l’émotion dominante
        if last_emotion in ["triste", "frustré", "fatigué", "angoissé"]:
            return "Voix E – calme, douce et réconfortante suggérée."
        elif last_emotion in ["stressé", "confus"]:
            return "Voix B – posée et rassurante conseillée."
        elif last_emotion in ["joyeux", "satisfait"]:
            return "Voix D – énergique et chaleureuse recommandée."

        # Base sur l’heure de la journée
        if hour < 7 or hour >= 22:
            return "Voix C – lente et apaisante suggérée pour un moment tardif."
        elif 12 <= hour <= 14:
            return "Voix A – claire et concise pour un moment actif."

        return "Voix standard – adaptée à une humeur neutre et une heure classique."

    def tell_random_joke(self, category: str = "any", path: str = "humour_bank.json") -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                jokes = json.load(f)
        except Exception as e:
            return f"Erreur de chargement des blagues : {e}"

        if category.lower() == "any":
            all_jokes = sum(jokes.values(), [])
            return random.choice(all_jokes) if all_jokes else "Aucune blague trouvée."

        selected = jokes.get(category.lower())
        if not selected:
            return f"Aucune blague dans la catégorie '{category}'. Essaie 'soft', 'nerdy' ou 'grandma_friendly'."
        return random.choice(selected)

    def say_reassurance(self, context: str, path: str = "reassurance_bank.json") -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                bank = json.load(f)
        except Exception as e:
            return f"Erreur de chargement de la base de réassurance : {e}"

        context = context.lower()
        if context in bank:
            return random.choice(bank[context])
        else:
            return "Je suis là si tu as besoin. Tu n’es pas seul."

    def teach_cyber_tip(self, topic: str = "any", path: str = "cybersecurity_bank.json") -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                bank = json.load(f)
        except Exception as e:
            return f"Erreur de chargement des conseils de cybersécurité : {e}"

        if topic.lower() == "any":
            all_tips = sum(bank.values(), [])
            return random.choice(all_tips) if all_tips else "Aucun conseil disponible."

        tips = bank.get(topic.lower())
        if not tips:
            return f"Aucun conseil dans la catégorie '{topic}'. Essaie 'passwords', 'phishing', 'updates' ou 'devices'."
        return random.choice(tips)

    def record_memory(self, user_id: str, event_type: str, event_description: str, path: str = None):
        if path is None:
            path = os.path.join(self._PROFILES_DIR, f"{user_id}_memories_log.json")

        memory = {
            "date": datetime.datetime.now().isoformat(),
            "type": event_type,
            "event": event_description
        }

        log = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception:
                pass

        log.append(memory)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4)

    def recall_memories(self, user_id: str, path: str = None, max_entries: int = 5) -> list:
        if path is None:
            path = os.path.join(self._PROFILES_DIR, f"{user_id}_memories_log.json")

        if not os.path.exists(path):
            return ["Aucun souvenir enregistré pour le moment."]

        try:
            with open(path, "r", encoding="utf-8") as f:
                log = json.load(f)
                return [f"{entry['date'][:10]} – {entry['event']}" for entry in log[-max_entries:]]
        except Exception as e:
            return [f"Erreur de lecture des souvenirs : {e}"]

    def record_voice_context(self, user_id: str, emotion: str, voice_id: str, result: str, path: str = None):
        if path is None:
            path = os.path.join(self._PROFILES_DIR, f"{user_id}_voice_trace.json")

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "emotion": emotion.lower(),
            "voice_id": voice_id,
            "result": result.lower()
        }

        log = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    log = json.load(f)
            except Exception:
                pass

        log.append(entry)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4)

    def summarize_voice_memory(self, user_id: str, path: str = None) -> dict:
        if path is None:
            path = os.path.join(self._PROFILES_DIR, f"{user_id}_voice_trace.json")

        if not os.path.exists(path):
            return {"message": "Aucune donnée vocale enregistrée."}

        try:
            with open(path, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception as e:
            return {"error": f"Erreur de lecture : {e}"}

        summary = {}
        for entry in log:
            voice = entry["voice_id"]
            result = entry["result"]
            if voice not in summary:
                summary[voice] = {"positif": 0, "négatif": 0}
            if result in summary[voice]:
                summary[voice][result] += 1

        return summary

    def play_voice_clip(self, voice_id: str, base_path: str = "voices"):
        import os
        try:
            import playsound
        except ImportError:
            print("Le module 'playsound' est requis pour jouer les voix.")
            return

        file = os.path.join(base_path, f"voice_{voice_id}.mp3")
        if os.path.exists(file):
            print(f"[Lecture] ➤ voice_{voice_id}.mp3")
            playsound.playsound(file)
        else:
            print(f"[Avertissement] Aucun fichier vocal trouvé pour la voix : {voice_id}")


if __name__ == "__main__":
    learner = INSFLocalLearner()
    print("Activation d’iAngel avec voix Sol...")
    learner.play_voice_clip("Sol")
