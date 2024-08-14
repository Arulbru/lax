from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import logging
import pickle
import os
import platform
import datetime
import re
import asyncio

# Inserisci il token del tuo bot Telegram
TELEGRAM_BOT_TOKEN = '7013999319:AAET7D5jqM3vrc1eG-zEYIoocBMMWmTuaNs'

# Lista degli ID utente autorizzati (aggiungi qui i tuoi ID)
AUTHORIZED_USERS = [5222500901]  # Sostituisci con il tuo ID utente o con gli ID degli utenti autorizzati

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

# Carica il modello e il vettorizzatore salvati
def load_model_and_vectorizer():
    try:
        with open('modello.pkl', 'rb') as model_file:
            model = pickle.load(model_file)
        logging.info("Modello caricato con successo.")
    except FileNotFoundError:
        logging.error("File del modello non trovato.")
        raise
    except Exception as e:
        logging.error(f"Errore durante il caricamento del modello: {e}")
        raise

    try:
        with open('vectorizer.pkl', 'rb') as vectorizer_file:
            vectorizer = pickle.load(vectorizer_file)
        logging.info("Vectorizer caricato con successo.")
    except FileNotFoundError:
        logging.error("File del vettorizzatore non trovato.")
        raise
    except Exception as e:
        logging.error(f"Errore durante il caricamento del vettorizzatore: {e}")
        raise

    return model, vectorizer

model, vectorizer = load_model_and_vectorizer()

def trova_risposta(comando: str) -> str:
    try:
        comando_vectorizzato = vectorizer.transform([comando])
        risposta = model.predict(comando_vectorizzato)
        
        if len(risposta) > 0 and isinstance(risposta[0], str):
            return risposta[0]
        else:
            logging.error(f"Tipo di dato inatteso: {type(risposta[0])}. Mi aspettavo una stringa.")
            return "Non conosco la risposta a questa domanda."
    except Exception as e:
        logging.error(f"Errore nella predizione: {e}")
        return "Si è verificato un errore durante l'elaborazione della tua richiesta."

def spegni_computer() -> str:
    try:
        if platform.system() == "Windows":
            os.system('shutdown /s /t 1')
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            os.system('shutdown now')
        else:
            return "Sistema operativo non supportato per lo spegnimento automatico."
        return "Il computer si sta spegnendo..."
    except Exception as e:
        logging.error(f"Errore durante lo spegnimento del computer: {e}")
        return "Si è verificato un errore durante lo spegnimento del computer."

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        await update.message.reply_text('Ciao! Sono LAX. Dimmi cosa posso fare per te.')
    else:
        await update.message.reply_text("Non sei autorizzato a usare questo bot.")

async def status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        status_message = "Il bot è attivo e funzionante."
        await update.message.reply_text(status_message)
    else:
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")

async def orario(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        now = datetime.datetime.now()
        ora_corrente = now.strftime("%H:%M:%S")
        await update.message.reply_text(f"L'ora corrente è: {ora_corrente}")
    else:
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")

async def set_reminder(update: Update, context: CallbackContext, reminder_time: str, reminder_message: str) -> None:
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        try:
            # Converte l'ora del promemoria in un oggetto datetime
            reminder_datetime = datetime.datetime.strptime(reminder_time, "%H:%M")
            now = datetime.datetime.now()

            # Calcola il tempo di attesa
            delay = (reminder_datetime - now).total_seconds()
            if delay < 0:
                delay += 86400  # Se l'orario è passato, imposta il promemoria per il giorno successivo

            await update.message.reply_text(f"Promemoria impostato per le {reminder_time}: {reminder_message}")
            
            await asyncio.sleep(delay)
            await context.bot.send_message(chat_id=user_id, text=f"Promemoria: {reminder_message}")

        except (IndexError, ValueError):
            await update.message.reply_text("Formato del comando non corretto. Usa /promemoria HH:MM messaggio.")
    else:
        await update.message.reply_text("Non sei autorizzato a usare questo comando.")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in AUTHORIZED_USERS:
        text = update.message.text.lower()
        logging.info(f"Messaggio ricevuto: {text}")

        # Gestione del comando di spegnimento
        if "spegni il computer" in text:
            risposta = spegni_computer()
            await update.message.reply_text(risposta)
        
        # Gestione del comando per conoscere l'ora
        elif "che ore sono" in text or "orario" in text:
            now = datetime.datetime.now()
            ora_corrente = now.strftime("%H:%M:%S")
            await update.message.reply_text(f"L'ora corrente è: {ora_corrente}")
        
        # Gestione del comando per impostare un promemoria
        elif "ricordami" in text and "alle" in text:
            # Estrazione del messaggio e dell'ora
            match = re.search(r"ricordami di (.+?) alle (\d{1,2}:\d{2})", text)
            if match:
                reminder_message = match.group(1)
                reminder_time = match.group(2)
                await set_reminder(update, context, reminder_time, reminder_message)
            else:
                await update.message.reply_text("Non sono riuscito a capire l'ora o il messaggio del promemoria.")
        
        # Altri comandi generici
        else:
            risposta = trova_risposta(text)
            await update.message.reply_text(risposta)
    else:
        await update.message.reply_text("Non sei autorizzato a usare questo bot.")

def main() -> None:
    # Crea l'applicazione del bot
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Gestore del comando /start
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("orario", orario))
    
    # Gestore dei messaggi di testo
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Avvia il bot
    application.run_polling()

if __name__ == "__main__":
    main()
