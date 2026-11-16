#!/usr/bin/env python3
"""
Gera a PRÉVIA com marca d'água de um convite da Creativy.

Uso:
  python3 previa.py <pasta-do-convite> --cliente "Ana Souza" [--dias 4] [--saida <pasta-do-repo-previas>]

O que faz:
  1. Copia o convite para <saida>/p/<codigo-aleatorio>/
  2. Grava a marca d'água dentro das imagens (png/jpg/webp) e dos vídeos (mp4), em baixa qualidade
  3. Injeta no index.html: marca na tela, validade (dias), bloqueio de cópia, noindex
     e desliga os botões de WhatsApp (confirmação de presença) na prévia
  4. Mostra o link final da prévia
O convite original NÃO é alterado.
"""
import argparse, os, re, secrets, shutil, subprocess, sys, datetime
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BASE = 'https://creativyconvites.com.br/previascreativy'   # endereço público do repositório de prévias

def tile(w, h, texto, alpha=70):
    """Camada transparente com o texto repetido na diagonal."""
    lado = max(w, h)
    big = Image.new('RGBA', (lado * 2, lado * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    tam = max(18, int(min(w, h) * 0.055))
    f = ImageFont.truetype(FONT, tam)
    passo_y = int(tam * 3.6)
    larg = int(d.textlength(texto, font=f)) + tam * 3
    for row, y in enumerate(range(0, lado * 2, passo_y)):
        for x in range(-larg, lado * 2, larg):
            ox = x + (larg // 2 if row % 2 else 0)
            d.text((ox + 2, y + 2), texto, font=f, fill=(0, 0, 0, alpha))
            d.text((ox, y), texto, font=f, fill=(255, 255, 255, alpha + 40))
    big = big.rotate(28, resample=Image.BICUBIC)
    cx, cy = lado, lado
    return big.crop((cx - w // 2, cy - h // 2, cx - w // 2 + w, cy - h // 2 + h))

def marca_imagem(path, texto):
    im = Image.open(path)
    animada = getattr(im, 'is_animated', False)
    if animada:
        return False
    ext = os.path.splitext(path)[1].lower()
    rgba = im.convert('RGBA')
    rgba = Image.alpha_composite(rgba, tile(*rgba.size, texto))
    if ext in ('.jpg', '.jpeg'):
        rgba.convert('RGB').save(path, quality=72)
    elif ext == '.png':
        rgba.save(path, optimize=True)
    else:
        rgba.save(path, quality=70, method=4)
    return True

def marca_video(path, texto, tmp):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                            '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')
    w, h = int(probe[0]), int(probe[1])
    esc = 540 / min(w, h)
    if esc < 1:
        w, h = int(w * esc) // 2 * 2, int(h * esc) // 2 * 2
    ov = os.path.join(tmp, 'ov.png')
    tile(w, h, texto, 80).save(ov)
    out = path + '.tmp.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-i', ov, '-filter_complex',
                    f'[0:v]scale={w}:{h}[v];[v][1:v]overlay=0:0', '-c:v', 'libx264', '-preset', 'fast', '-crf', '30',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '64k', out], check=True)
    os.replace(out, path)

INJETA = r'''
<meta name="robots" content="noindex,nofollow">
<style>
#cv-prev{position:fixed;left:0;right:0;bottom:0;z-index:2147483647;pointer-events:none;text-align:center;padding:6px 10px calc(6px + env(safe-area-inset-bottom,0px));background:rgba(0,0,0,.72);color:#fff;font:600 12px/1.3 system-ui,sans-serif;letter-spacing:.03em}
#cv-exp{position:fixed;inset:0;z-index:2147483647;background:#111;color:#fff;display:none;align-items:center;justify-content:center;text-align:center;padding:30px;font:500 18px/1.5 system-ui,sans-serif}
#cv-toast{position:fixed;left:50%;top:18%;transform:translateX(-50%);z-index:2147483647;background:rgba(0,0,0,.85);color:#fff;padding:12px 18px;border-radius:14px;font:500 15px/1.35 system-ui,sans-serif;max-width:80%;text-align:center;opacity:0;transition:opacity .25s;pointer-events:none}
img,video{-webkit-user-drag:none;user-select:none;-webkit-touch-callout:none}
</style>
<script>
(function(){
  var CLIENTE=__CLIENTE__,FIM=__FIM__;
  function bar(){var b=document.createElement('div');b.id='cv-prev';b.textContent='PRÉVIA • Creativy • '+CLIENTE+' • válida até '+new Date(FIM).toLocaleDateString('pt-BR')+' • não é o convite final';document.body.appendChild(b);
    var t=document.createElement('div');t.id='cv-toast';document.body.appendChild(t);window.__cvToast=function(m){t.textContent=m;t.style.opacity=1;clearTimeout(t._h);t._h=setTimeout(function(){t.style.opacity=0},2600)}}
  function expira(){var e=document.createElement('div');e.id='cv-exp';e.innerHTML='<div>Esta prévia expirou.<br>Fale com a Creativy para receber o convite final.<br><br><small>@creativy.convites</small></div>';document.body.appendChild(e);e.style.display='flex';
    document.querySelectorAll('video,audio').forEach(function(m){try{m.pause();m.removeAttribute('src');m.load()}catch(x){}});
    document.documentElement.style.overflow='hidden'}
  function ini(){bar();if(Date.now()>FIM)expira()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ini);else ini();
  setInterval(function(){if(Date.now()>FIM&&!document.getElementById('cv-exp'))expira()},30000);
  /* sem copiar/salvar */
  ['contextmenu','dragstart','selectstart'].forEach(function(ev){document.addEventListener(ev,function(e){e.preventDefault()})});
  /* na prévia, confirmação por WhatsApp fica desligada */
  var _open=window.open;
  window.open=function(u){if(typeof u==='string'&&/wa\.me|whatsapp/i.test(u)){window.__cvToast&&window.__cvToast('Na prévia a confirmação por WhatsApp fica desligada. Ela funciona no convite final.');return null}return _open.apply(window,arguments)};
  document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(a&&/wa\.me|whatsapp/i.test(a.getAttribute('href'))){e.preventDefault();e.stopPropagation();window.__cvToast&&window.__cvToast('Na prévia a confirmação por WhatsApp fica desligada. Ela funciona no convite final.')}},true);
})();
</script>
'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pasta')
    ap.add_argument('--cliente', required=True)
    ap.add_argument('--dias', type=int, default=4)
    ap.add_argument('--saida', default=os.path.expanduser('/home/claude/previas-repo'))
    a = ap.parse_args()
    if not os.path.isfile(os.path.join(a.pasta, 'index.html')):
        sys.exit('Não achei index.html em ' + a.pasta)
    cod = secrets.token_hex(4)
    dest = os.path.join(a.saida, 'p', cod)
    shutil.copytree(a.pasta, dest, ignore=shutil.ignore_patterns('.git', '.github', 'node_modules', '__pycache__'))
    texto = f'PRÉVIA • CREATIVY • {a.cliente.upper()}'
    tmp = os.path.join(dest, '.tmp'); os.makedirs(tmp, exist_ok=True)
    n_img = n_vid = 0
    for raiz, _, arqs in os.walk(dest):
        if raiz.startswith(tmp): continue
        for nome in arqs:
            p = os.path.join(raiz, nome); ext = os.path.splitext(nome)[1].lower()
            if ext in ('.png', '.jpg', '.jpeg', '.webp'):
                if os.path.basename(p) in ('favicon.png',): continue
                try: n_img += marca_imagem(p, texto)
                except Exception as e: print('  aviso (imagem):', nome, e)
            elif ext in ('.mp4', '.mov', '.m4v'):
                try: marca_video(p, texto, tmp); n_vid += 1
                except Exception as e: print('  aviso (vídeo):', nome, e)
    shutil.rmtree(tmp, ignore_errors=True)
    idx = os.path.join(dest, 'index.html')
    h = open(idx, encoding='utf-8').read()
    fim = int((datetime.datetime.now() + datetime.timedelta(days=a.dias)).timestamp() * 1000)
    inj = INJETA.replace('__CLIENTE__', repr(a.cliente).replace("'", '"')).replace('__FIM__', str(fim))
    if '<head>' in h: h = h.replace('<head>', '<head>' + inj, 1)
    else: h = inj + h
    open(idx, 'w', encoding='utf-8').write(h)
    # impede o Google de listar
    open(os.path.join(a.saida, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
    open(os.path.join(a.saida, 'index.html'), 'a').close()
    reg = os.path.join(a.saida, 'registro.csv')
    novo = not os.path.exists(reg)
    with open(reg, 'a', encoding='utf-8') as f:
        if novo: f.write('codigo,cliente,criada_em,valida_ate,status\n')
        f.write(f"{cod},{a.cliente},{datetime.date.today()},{(datetime.date.today()+datetime.timedelta(days=a.dias))},previa enviada\n")
    print(f'Prévia pronta: {n_img} imagens e {n_vid} vídeos com marca.')
    print(f'Link: {BASE}/p/{cod}/')
    print(f'Válida por {a.dias} dias.')

if __name__ == '__main__':
    main()
