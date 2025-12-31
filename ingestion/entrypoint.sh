#!/bin/sh
ollama serve &
sleep 5
ollama pull nomic-embed-text
ollama pull ${LANGUAGE_MODEL}
wait
