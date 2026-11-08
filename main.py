import os
import json
import random
import asyncio
from datetime import time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
ADMIN = int(os.environ["ADMIN_ID"])

FILE = "fotos.json"

def cargar():
    if os.path.exists(FILE):
        with open(FILE, "r") as f:
            return json.load(f)
    return []

def guardar(datos):
    with open(FILE, "w") as f:
        json.dump(datos, f)

def autorizado(update):
    return update.effective_user.id == ADMIN

async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    await update.message.reply_text(
        "¡Hola! 📸\n"
        "/add - Añadir una foto con texto\n"
        "/list - Ver tus fotos\n"
        "/delete ID - Borrar una foto\n"
        "/cancel - Cancelar"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    context.user_data["esperando_foto"] = True
    await update.message.reply_text(
        "Envíame una foto con el texto que quieras publicar."
    )

async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.user_data.get("esperando_foto"):
        return
    if not update.message.photo:
        await update.message.reply_text("Envíame una foto.")
        return

    datos = cargar()
    datos.append({
        "id": max([x["id"] for x in datos], default=0) + 1,
        "foto": update.message.photo[-1].file_id,
        "texto": update.message.caption or ""
    })
    guardar(datos)
    context.user_data["esperando_foto"] = False
    await update.message.reply_text("✅ Foto guardada.")

async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    datos = cargar()
    if not datos:
        await update.message.reply_text("Todavía no tienes fotos.")
        return
    texto = "\n".join(
        f'ID {x["id"]}: {x["texto"][:40]}'
        for x in datos
    )
    await update.message.reply_text(texto[:4000])

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not autorizado(update):
        return
    if not context.args:
        await update.message.reply_text("Usa /delete ID")
        return
    try:
        numero = int(context.args[0])
        datos = [x for x in cargar() if x["id"] != numero]
        guardar(datos)
        await update.message.reply_text("Foto borrada si existía.")
    except ValueError:
        await update.message.reply_text("El ID debe ser un número.")

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["esperando_foto"] = False
    await update.message.reply_text("Cancelado.")

async def publicar(context: ContextTypes.DEFAULT_TYPE):
    datos = cargar()
    if len(datos) < 30:
        print("Necesitas al menos 30 fotos.")
        return

    seleccion = random.sample(datos, 30)

    for foto in seleccion:
        await context.bot.send_photo(
            chat_id=CHANNEL,
            photo=foto["foto"],
            caption=foto["texto"]
        )
        await asyncio.sleep(5)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", inicio))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", lista))
    app.add_handler(CommandHandler("delete", borrar))
    app.add_handler(CommandHandler("cancel", cancelar))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_foto))

    app.job_queue.run_daily(
        publicar,
        time=time(16, 0, tzinfo=ZoneInfo("Europe/Madrid"))
    )

    app.run_polling()

if __name__ == "__main__":
    main()
