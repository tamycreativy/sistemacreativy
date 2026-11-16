# Sistema Creativy

Ferramentas internas da Creativy.

## Prévia com marca d'água (`previa.py`)

Gera uma cópia do convite com marca d'água gravada nas imagens e vídeos, validade em dias,
bloqueio de cópia e WhatsApp desligado, pronta para subir no repositório `previascreativy`.

```
python3 previa.py <pasta-do-convite> --cliente "Nome do cliente" [--dias 4] [--saida <pasta-do-repo-previascreativy>]
```

Fluxo de cada pedido:
1. Cliente paga 50% de entrada → começa a criação.
2. No dia da entrega: gerar a prévia (`previa.py`), subir no `previascreativy` e mandar o link.
3. Cliente aprova e envia o comprovante dos outros 50%.
4. Só então subir o convite limpo (sem marca) no repositório do cliente e enviar o link final.
5. Atualizar o `registro.csv` do `previascreativy` (status: aprovada / quitada).
