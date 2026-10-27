"""The Legend of Commits: NES-inspired GitHub contribution overworld.

Version 6: NES source tiles, automatic shield defense, cardinal rock and spear
projectiles, roaming enemies, item pickups, and cave entrances.

The animated 53 x 7 contribution heatmap IS the overworld, not a second scene.
Standard library only; GitHub Actions provides GH_TOKEN.
Characters/items fetched from NESMaps (Nintendo-owned game artwork).
For NES-accurate scenery provide source 16x16 NES tiles in --asset-dir
as bush.png/tree.png/rock.png/cave.png, and rock_projectile.png.
--require-scenery rejects any missing originals; no stand-ins are used then.
Run --demo to preview offline without contacting GitHub.
"""

import argparse
import base64
import time
from collections import deque
from datetime import date, timedelta
from html import escape
import json
import heapq
import random
import struct
import zlib
from bisect import bisect_right
import os
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

USERNAME = 'drabhikroy'
# Walking pace is preserved at roughly one tile per second. The total
# cycle grows with the route instead of making Link speed up to fit 86 s.
WALK_SECONDS = 0.96
PITCH = 16                 # One native NES 16px tile per contribution day.
CELL = 16
LEFT, TOP = 28, 163
COLORS = {
    'NONE': '#243426',
    'FIRST_QUARTILE': '#355c37',
    'SECOND_QUARTILE': '#508341',
    'THIRD_QUARTILE': '#7eab53',
    'FOURTH_QUARTILE': '#c1d67a',
}
INK, GOLD, CREAM = '#10151b', '#f1d071', '#f2e5b5'
# Compact, transparent pixel-art wordmark derived from the approved
# THE LEGEND OF COMMITS illustration. Embedded here so the generated SVG
# is self-contained and the daily workflow requires no extra logo file.
COMMITS_WORDMARK_B64 = (
    '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'
    'QmCC'
)


def title_header():
    # The full wordmark has transparent padding on every side, so no letter
    # touches the viewport edge. There is no side Triforce.
    wordmark = ''.join(COMMITS_WORDMARK_B64)
    artwork = (
        '<g id="commits-logo">'
        '<image x="22" y="29" width="323" height="70" '
        'preserveAspectRatio="xMinYMin meet" image-rendering="pixelated" '
        f'href="data:image/png;base64,{wordmark}"/>'
        '</g>'
    )
    return text(22, 26, 'THE LEGEND OF', 13, GOLD, 'class="label"') + artwork

QUERY = '''query($login:String!){user(login:$login){contributionsCollection{
  contributionCalendar{totalContributions weeks{contributionDays{
    date weekday contributionCount contributionLevel
  }}}
}}}'''


# These are the *original* 1986 Nintendo sprites, not assistant-drawn substitutes.
# Source: https://nesmaps.com/maps/Zelda/sprites/ZeldaSprites.html
# The art belongs to Nintendo. Consider that before publishing these in a public README.
NES_SOURCE = 'https://www.nesmaps.com/maps/Zelda/sprites/'
NES_SPRITES = {
    'link_D': ('ZeldaSpriteLinkFront.gif', 15, 16),
    'link_U': ('ZeldaSpriteLinkBack.gif', 15, 16),
    'link_L': ('ZeldaSpriteLinkLeft.gif', 15, 16),
    'link_R': ('ZeldaSpriteLinkRight.gif', 15, 16),
    'octorok': ('ZeldaSpriteOctorokRedDown.gif', 16, 16),
    'moblin': ('ZeldaSpriteMolblinRedFront.gif', 16, 16),
    'tektite': ('ZeldaSpriteTektiteRed.gif', 16, 15),
    'octorok_blue': ('ZeldaSpriteOctorokBlueDown.gif', 16, 16),
    'moblin_blue': ('ZeldaSpriteMolblinBlueFront.gif', 16, 16),
    'tektite_blue': ('ZeldaSpriteTektiteBlue.gif', 16, 15),
    'heart': ('ZeldaSpriteHeart.gif', 7, 8),
    'fairy': ('ZeldaSpriteFairy.gif', 8, 16),
    'heart_container': ('ZeldaSpriteHeartContainer.png', 13, 13),
    'clock': ('ZeldaSpriteClock.png', 11, 16),
    'key': ('ZeldaSpriteKey.png', 8, 16),
    'bomb': ('ZeldaSpriteBomb.png', 8, 14),
    'rupee_blue': ('ZeldaSprite5Rupies.png', 8, 16),
    'rupee': ('ZeldaSpriteRupy.gif', 8, 16),
    'triforce': ('ZeldaSpriteTriforce.gif', 10, 10),
    'peahat': ('ZeldaSpritePeahat.gif', 16, 16),
    'leever_red': ('ZeldaSpriteLeeverRed.gif', 16, 16),
    'leever_blue': ('ZeldaSpriteLeeverBlue.gif', 16, 16),
    # Extra *original NES* directions. The previous generator displayed
    # all Octoroks looking down and all Moblins looking at the viewer.
    'octorok_U': ('ZeldaSpriteOctorokRedUp.gif', 16, 16),
    'octorok_L': ('ZeldaSpriteOctorokRedLeft.gif', 16, 16),
    'octorok_R': ('ZeldaSpriteOctorokRedRight.gif', 16, 16),
    'octorok_blue_U': ('ZeldaSpriteOctorokBlueUp.gif', 16, 16),
    'octorok_blue_L': ('ZeldaSpriteOctorokBlueLeft.gif', 16, 16),
    'octorok_blue_R': ('ZeldaSpriteOctorokBlueRight.gif', 16, 16),
    'moblin_U': ('ZeldaSpriteMolblinRedBack.gif', 16, 16),
    'moblin_L': ('ZeldaSpriteMolblinRedLeft.gif', 16, 16),
    'moblin_R': ('ZeldaSpriteMolblinRedRight.gif', 16, 16),
    'moblin_blue_U': ('ZeldaSpriteMolblinBlueBack.gif', 16, 16),
    'moblin_blue_L': ('ZeldaSpriteMolblinBlueLeft.gif', 16, 16),
    'moblin_blue_R': ('ZeldaSpriteMolblinBlueRight.gif', 16, 16),

    'link_thrust_D': ('ZeldaSpriteLinkSwingSwordFront.png', 16, 27),
    'link_thrust_U': ('ZeldaSpriteLinkSwingSwordBack.png', 16, 27),
    'link_thrust_L': ('ZeldaSpriteLinkSwingSwordLeft.png', 27, 16),
    'link_thrust_R': ('ZeldaSpriteLinkSwingSwordRight.png', 27, 16),
}



# NESMaps item art often has an opaque black rectangle. Convert GIF/PNG
# assets to transparent RGBA PNG using only Python's standard library.
# Retain dark pixels bordering colored sprite art, but erase black fill
# from the surrounding canvas. This also works in GitHub Actions.
def _png_chunks(data):
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Not PNG')
    off=8
    while off < len(data):
        n=int.from_bytes(data[off:off+4],'big'); typ=data[off+4:off+8]
        chunk=data[off+8:off+8+n]
        yield typ,chunk
        off+=n+12
        if typ==b'IEND':break


def _rgba_from_png(raw):
    chunks=list(_png_chunks(raw))
    ihdr=next(x for k,x in chunks if k==b'IHDR')
    w,h,depth,ctype,comp,filt,interlace=struct.unpack('>IIBBBBB',ihdr)
    if depth!=8 or interlace!=0 or w>64 or h>64:
        raise ValueError('Unsupported PNG pixel layout')
    ncomp={0:1,2:3,3:1,4:2,6:4}[ctype]
    compressed=b''.join(x for k,x in chunks if k==b'IDAT')
    decoded=zlib.decompress(compressed)
    stride=w*ncomp
    prev=bytearray(stride);i=0;pixels=[]
    for y in range(h):
        f=decoded[i]; i+=1
        cur=bytearray(decoded[i:i+stride]); i+=stride
        for j in range(stride):
            a=cur[j-ncomp] if j>=ncomp else 0
            b=prev[j];c=prev[j-ncomp] if j>=ncomp else 0
            if f==1: pred=a
            elif f==2:pred=b
            elif f==3:pred=(a+b)//2
            elif f==4:
                p=a+b-c;da=abs(p-a);db=abs(p-b);dc=abs(p-c)
                pred=a if da<=db and da<=dc else b if db<=dc else c
            elif f==0:pred=0
            else:raise ValueError('Bad PNG filter')
            cur[j]=(cur[j]+pred)&255
        pixels.extend(cur[j:j+ncomp] for j in range(0,stride,ncomp))
        prev=cur
    pal=next((x for k,x in chunks if k==b'PLTE'),b'')
    transparency=next((x for k,x in chunks if k==b'tRNS'),b'')
    out=[]
    for px in pixels:
        if ctype==6:out.append(tuple(px))
        elif ctype==2:out.append((*px,255))
        elif ctype==3:
            ix=px[0];out.append((*pal[ix*3:ix*3+3], transparency[ix] if ix<len(transparency) else 255))
        elif ctype==0:out.append((px[0],)*3+(255,))
        else:out.append((px[0],)*3+(px[1],))
    return w,h,out


def _rgba_from_gif(raw):
    if not raw.startswith((b'GIF89a',b'GIF87a')):
        raise ValueError('Not GIF')
    w,h,packed,bg,aspect=struct.unpack_from('<HHBBB',raw,6)
    if w>64 or h>64:raise ValueError('GIF too large')
    cursor=13
    def palette(packed):
        nonlocal cursor
        n=3*(2**((packed&7)+1))
        blob=raw[cursor:cursor+n];cursor+=n
        return [tuple(blob[i:i+3]) for i in range(0,len(blob),3)]
    colors=palette(packed) if packed&128 else []
    transparent=None
    def blocks():
        nonlocal cursor
        data=bytearray()
        while True:
            sz=raw[cursor];cursor+=1
            if sz==0:break
            data.extend(raw[cursor:cursor+sz]);cursor+=sz
        return bytes(data)
    while cursor<len(raw):
        marker=raw[cursor];cursor+=1
        if marker==0x21:
            label=raw[cursor];cursor+=1
            if label==0xF9:
                sz=raw[cursor]; cursor+=1
                fields=raw[cursor:cursor+sz];cursor+=sz
                if fields[0]&1:transparent=fields[3]
                cursor+=1
            else:blocks()
        elif marker==0x2C:
            left,top,iw,ih,flags=struct.unpack_from('<HHHHB',raw,cursor);cursor+=9
            pal=palette(flags) if flags&128 else colors
            min_code=raw[cursor];cursor+=1
            compressed=blocks()
            bits=0;acc=0; pos=0
            clear=1<<min_code; end=clear+1; width=min_code+1
            next_code=end+1; table={i:bytes([i]) for i in range(clear)}
            old=None;values=bytearray()
            def getbits(n):
                nonlocal bits,acc,pos
                while bits<n:
                    if pos>=len(compressed):return None
                    acc|=compressed[pos]<<bits;bits+=8;pos+=1
                code=acc&((1<<n)-1);acc>>=n;bits-=n
                return code
            while True:
                code=getbits(width)
                if code is None or code==end:break
                if code==clear:
                    table={i:bytes([i]) for i in range(clear)}
                    next_code=end+1;width=min_code+1;old=None
                    continue
                if code in table:item=table[code]
                elif code==next_code and old is not None:item=old+old[:1]
                else:raise ValueError('Invalid GIF LZW')
                values.extend(item)
                if old is not None and next_code<4096:
                    table[next_code]=old+item[:1];next_code+=1
                    if next_code==(1<<width) and width<12:width+=1
                old=item
                if len(values)>=iw*ih:break
            if len(values)<iw*ih:raise ValueError('Incomplete GIF')
            output=[(0,0,0,0)]*(w*h)
            if flags&64:
                offsets=[];idx=0
                for start,step in ((0,8),(4,8),(2,4),(1,2)):
                    for row in range(start,ih,step):offsets.append(row)
            else:offsets=list(range(ih))
            ix=0
            for row in offsets:
                for x in range(iw):
                    ci=values[ix];ix+=1
                    if row+top>=h or x+left>=w:continue
                    rgb=pal[ci] if ci<len(pal) else (0,0,0)
                    output[(row+top)*w+x+left]=(*rgb, 0 if ci==transparent else 255)
            return w,h,output
        elif marker==0x3B:break
        else:raise ValueError(f'Unknown GIF block {marker}')
    raise ValueError('No GIF frame')


def _rgba_png_bytes(w,h,pixels):
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    b=bytearray()
    for y in range(h):
        b.append(0)
        for rgba in pixels[y*w:(y+1)*w]:b.extend(rgba)
    return (b'\x89PNG\r\n\x1a\n'
            +chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))
            +chunk(b'IDAT',zlib.compress(bytes(b),9))+chunk(b'IEND',b''))


def remove_sprite_backdrop(raw):
    """Clear only the *exterior* solid dark backdrop.

    A flood fill from transparent/canvas edges leaves enclosed dark outlines,
    pupils, holes and colored pixels unchanged. Original transparency is
    respected. The old per-pixel heuristic erased interior details.
    """
    w, h, pixels = (_rgba_from_gif(raw) if raw.startswith(b'GIF8')
                    else _rgba_from_png(raw))
    from collections import deque as _deque
    def back(p): return p[3] == 0 or max(p[:3]) <= 22
    q = _deque()
    selected = set()
    for x in range(w):
        for y in (0,h-1):
            i=y*w+x
            if back(pixels[i]) and i not in selected:
                selected.add(i);q.append(i)
    for y in range(h):
        for x in (0,w-1):
            i=y*w+x
            if back(pixels[i]) and i not in selected:
                selected.add(i);q.append(i)
    while q:
        i=q.popleft();x=i%w;y=i//w
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx=x+dx;ny=y+dy
            if not (0<=nx<w and 0<=ny<h): continue
            j=ny*w+nx
            if j not in selected and back(pixels[j]):
                selected.add(j);q.append(j)
    result=[(0,0,0,0) if i in selected else p for i,p in enumerate(pixels)]
    return _rgba_png_bytes(w,h,result),w,h

def load_sprite_assets(asset_dir=None, require_scenery=False):
    """Embed original sprite pixels; download with retries or use saved files.

    Files may be supplied in --asset-dir if the sprite host is ever unavailable.
    Never silently replace a missing NES sprite with a made-up approximation.
    """
    legacy_cache = Path('assets/nes-original')
    asset_dir = (Path(asset_dir) if asset_dir else legacy_cache if legacy_cache.exists()
                 else Path(__file__).resolve().parent / 'assets' / 'nes-original')
    images = {}
    for name, (filename, width, height) in NES_SPRITES.items():
        local_file = asset_dir / filename
        if local_file.is_file():
            raw = local_file.read_bytes()
        else:
            raw = None
            for attempt in range(3):
                try:
                    request = Request(
                        NES_SOURCE + filename,
                        headers={'User-Agent': 'Mozilla/5.0 (compatible; ZeldaContributionGraph/1.0)'})
                    with urlopen(request, timeout=20) as response:
                        raw = response.read(1_000_001)
                    if len(raw) > 1_000_000:
                        raise ValueError('Unusually large sprite response')
                    break
                except Exception as exc:
                    if attempt == 2:
                        raise RuntimeError(
                            f'Cannot retrieve original NES sprite {filename} from {NES_SOURCE}. '
                            f'Place it in {asset_dir}/ and rerun. Cause: {exc}') from exc
                    time.sleep(attempt + 1)
        if not local_file.is_file():
            try:
                asset_dir.mkdir(parents=True, exist_ok=True)
                local_file.write_bytes(raw)
            except OSError:
                pass   # Still render SVG if asset cache is read-only.
        if raw.startswith((b'GIF87a', b'GIF89a')):
            mime = 'image/gif'
            actual_width = int.from_bytes(raw[6:8], 'little')
            actual_height = int.from_bytes(raw[8:10], 'little')
        elif raw.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = 'image/png'
            actual_width = int.from_bytes(raw[16:20], 'big')
            actual_height = int.from_bytes(raw[20:24], 'big')
        else:
            raise ValueError(f'{name}: image is not GIF or PNG: {filename}')
        # NES sprite frames are not all the same size. Preserve each GIF's
        # native dimensions rather than rejecting it or stretching it.
        if not (1 <= actual_width <= 64 and 1 <= actual_height <= 64):
            raise ValueError(
                f'{name}: unexpected GIF dimensions {actual_width}x{actual_height}'
            )
        if (actual_width, actual_height) != (width, height):
            print(
                f'Note: {name} is {actual_width}x{actual_height} '
                f'(reference {width}x{height}); retaining original dimensions.'
            )
        if name in {'heart','heart_container','fairy','bomb','key','clock',
                    'rupee','rupee_blue','triforce'}:
            try:
                raw, actual_width, actual_height = remove_sprite_backdrop(raw)
                mime='image/png'
            except (ValueError, KeyError, IndexError, struct.error) as exc:
                print(f'Warning: could not clean background of {filename}: {exc}')
        images[name] = (
            f'data:{mime};base64,{base64.b64encode(raw).decode("ascii")}',
            actual_width,
            actual_height,
        )
    # Optional original NES overworld and projectile tiles. Crop them
    # from a legitimate NES tileset and place these files beside the GIFs.
    # The files are never required for ordinary preview or GitHub Actions.
    for kind in ('bush','tree','rock','cave','rock_projectile','spear_projectile'):
        for suffix, mime, header in (
            ('.png','image/png',b'\x89PNG\r\n\x1a\n'),
            ('.gif','image/gif',b'GIF8'),
        ):
            local = asset_dir / f'{kind}{suffix}'
            if not local.is_file():
                continue
            raw = local.read_bytes()
            if len(raw) > 100_000 or not raw.startswith(header):
                raise ValueError(f'Invalid scenery image: {local}')
            if suffix == '.png':
                width,height = [int.from_bytes(raw[i:i+4],'big') for i in (16,20)]
            else:
                width,height = [int.from_bytes(raw[i:i+2],'little') for i in (6,8)]
            # Never resample NES source artwork: only 16x16 tiles are accepted.
            # Projectiles are allowed to be smaller than a whole tile.
            if kind in ('rock_projectile','spear_projectile'):
                valid = 2 <= width <= 16 and 2 <= height <= 16
            else:
                valid = width == height == 16
            if not valid:
                raise ValueError(
                    f'{local}: expected original 16x16 NES terrain tile '
                    '(projectile may be smaller); '
                    f'got {width}x{height}')
            images[kind]=(f'data:{mime};base64,{base64.b64encode(raw).decode("ascii")}',width,height)
            break
    missing = sorted(set(('bush','tree','rock','cave','rock_projectile','spear_projectile')) - set(images))
    if missing:
        message=('NES source tiles not supplied: '+ ', '.join(missing) +
                 '. The preview uses approximate fallback scenery.')
        if require_scenery:
            raise RuntimeError(message + ' Supply bush.png, tree.png, rock.png, cave.png, rock_projectile.png, spear_projectile.png under --asset-dir.')
        print(message)
    return images


def exact_sprite(images, name, cx, cy, opacity='1'):
    uri,w,h = images[name]
    return (f'<image x="{cx-w/2:g}" y="{cy-h/2:g}" width="{w}" height="{h}" '
            f'preserveAspectRatio="none" image-rendering="pixelated" opacity="{opacity}" href="{uri}"/>')


def get_calendar():
    token = os.environ.get('GH_TOKEN')
    if not token:
        raise RuntimeError('GH_TOKEN is required (GitHub Actions sets this). Use --demo locally.')
    request = Request('https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': USERNAME}}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'User-Agent': 'legend-of-commits'}, method='POST')
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get('errors'):
        raise RuntimeError(str(payload['errors']))
    user = (payload.get('data') or {}).get('user')
    if not user:
        raise RuntimeError(f'GitHub user {USERNAME!r} was not returned')
    return user['contributionsCollection']['contributionCalendar']


def demo_calendar(kind='mixed', columns=53):
    weeks, total = [], 0
    levels = list(COLORS)
    first = date(2025, 10, 26)
    for c in range(columns):
        days = []
        for r in range(7):
            k = (c*17 + r*11 + c*r*3) % 19
            if kind == 'empty':
                count = 0
            elif kind == 'dense':
                count = k + 1
            elif c < 27:
                count = k % 8 if c in (19, 25) and r in (2, 4) else 0
            elif c < 39:
                count = k % 9 if k % 7 == 0 else 0
            elif c < 46:
                count = k % 11 if k % 4 else 0
            else:
                count = k % 13 if k % 5 else 0
            total += count
            level = levels[min(4, 1 + count // 4)] if count else 'NONE'
            days.append({'date': (first + timedelta(days=7*c+r)).isoformat(),
                         'weekday': r, 'contributionCount': count,
                         'contributionLevel': level})
        weeks.append({'contributionDays': days})
    return {'weeks': weeks, 'totalContributions': total}


def box(x, y, w, h, color, attrs=''):
    return (f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
            f'fill="{color}" {attrs}/>')


def text(x, y, words, size=10, color=CREAM, attrs=''):
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}" {attrs}>{escape(str(words))}</text>'


def neighbors(cell, cols):
    r, c = cell
    for n in ((r,c+1), (r+1,c), (r,c-1), (r-1,c)):
        if 0 <= n[0] < 7 and 0 <= n[1] < cols:
            yield n


def find_path(start, goal, blocked, cols):
    queue = deque([start])
    previous = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for other in neighbors(current, cols):
            if other not in blocked and other not in previous:
                previous[other] = current
                queue.append(other)
    if goal not in previous:
        raise RuntimeError(f'Could not navigate from {start} to {goal}')
    path = []
    while goal is not None:
        path.append(goal)
        goal = previous[goal]
    return path[::-1]


def return_via_south(start, obstacles, cols):
    """Loop from the far edge back via southern open routes, not a teleport.

    The path consists entirely of orthogonal 15px steps and never enters a
    blocked cell. Low travel cost along row 5 encourages a return itinerary
    distinct from the forward journey without clearing scenery.
    """
    target=(3,0)
    goals=[(5,cols-1),(5,0),target]
    current=start
    steps=[]
    def scenic_path(a,b):
        heap=[(0,a)]
        dist={a:0}
        previous={a:None}
        while heap:
            d,node=heapq.heappop(heap)
            if d!=dist[node]: continue
            if node==b: break
            for nxt in neighbors(node,cols):
                if nxt in obstacles: continue
                # Favor row 5 for the trip back; avoid row 3 where possible.
                weight=1.0+0.25*abs(nxt[0]-5)
                nd=d+weight
                if nd<dist.get(nxt,float('inf')):
                    dist[nxt]=nd
                    previous[nxt]=node
                    heapq.heappush(heap,(nd,nxt))
        if b not in previous:
            raise RuntimeError('Unable to complete the continuous return patrol')
        result=[]
        at=b
        while at is not None:
            result.append(at)
            at=previous[at]
        return result[::-1]
    for goal in goals:
        leg=scenic_path(current,goal)
        steps.extend(leg[1:])
        current=goal
    assert current==target
    return steps


def make_map(calendar):
    """Keep the contributions in their existing 53x7 grid. Plan actual encounters.

    Each enemy encounter is a stationary pause on a free adjacent tile.
    Link faces the occupied enemy cell, thrusts the sword forward, and then continues his route.
    The route never enters a blocked contribution square.
    """
    weeks = calendar['weeks']
    cols = len(weeks)
    if cols < 12:
        raise ValueError('Calendar has too few weeks')
    days = {}
    for c, week in enumerate(weeks):
        for day in week['contributionDays']:
            days[(int(day['weekday']), c)] = day

    obstacles = {}
    for r in range(7):
        for c in range(2, cols - 2):
            if (r, c) not in days:
                continue
            roll = (c*37 + r*53 + (c*r)%19) % 47
            if roll in (3, 11, 27, 33, 41):
                obstacles[(r,c)] = ('bush','tree','rock','bush','rock')[
                    (3, 11, 27, 33, 41).index(roll)]

    # The original game's common overworld foes. Blue Octoroks require
    # two sword hits; other variants are currently one-hit encounters.
    enemy_positions = [
        ((2, max(5, cols//7)), 'octorok'),
        ((2, cols//4), 'octorok_blue'),
        ((2, cols//3), 'moblin'),
        ((4, cols//2), 'tektite'),
        ((1, 5*cols//8), 'tektite_blue'),
        ((2, 3*cols//4), 'moblin_blue'),
        ((2, 5*cols//6), 'peahat'),
        ((4, 2*cols//5), 'leever_red'),
        ((4, 4*cols//5), 'leever_blue'),
    ]
    for cell, kind in enemy_positions:
        obstacles[cell] = kind
    # Entrances are cut into rocky cliffs. Each cave occupies a real date
    # cell, while adjoining rock cells form its wall (not a hole in trees).
    for col in (cols//4, 3*cols//4):
        obstacles[(0,col)]='cave'
        for c in range(max(2,col-2),min(cols-2,col+3)):
            if c != col:
                obstacles[(0,c)]='rock'
        for c in (col-2,col+2):
            if 2<=c<cols-2:
                obstacles[(1,c)]='rock'
    for c in range(0, cols, 11):
        for r in (2, 3, 4):
            obstacles.pop((r,c), None)
    # Enemy squares remain solid and are never cleared for passage.
    for cell, kind in enemy_positions:
        obstacles[cell] = kind

    start, finish = (3,0), (3,cols-1)
    # Chronological encounter order, interleaved with ordinary waypoints.
    objectives = []
    for c in range(6, cols-1, 6):
        ideal = (2,4,3)[(c//6) % 3]
        objectives.append((c, 'waypoint', ideal))
    for enemy, kind in enemy_positions:
        objectives.append((enemy[1], 'enemy', (enemy,kind)))
    objectives.sort(key=lambda entry:(entry[0],entry[1] == 'waypoint'))
    objectives.append((cols-1, 'finish', finish))

    def compute():
        route = [start]
        attacks = []
        for c, typ, item in objectives:
            if typ == 'enemy':
                enemy, kind = item
                candidates = []
                for target in neighbors(enemy, cols):
                    if target in obstacles:
                        continue
                    try:
                        segment = find_path(route[-1], target, obstacles, cols)
                    except RuntimeError:
                        continue
                    # Prefer positions within the open corridor.
                    candidates.append((len(segment), abs(target[0]-3), target, segment))
                if not candidates:
                    raise RuntimeError(f'No accessible neighbor beside {enemy}')
                _,_,target,segment = min(candidates)
                route.extend(segment[1:])
                # Stay still for four animation frames. At the first hold,
                # Link turns toward the enemy, thrusts, then retracts.
                arrive = len(route)-1
                route.extend([target]*4)
                dr = enemy[0]-target[0]
                dc = enemy[1]-target[1]
                face = 'R' if dc == 1 else 'L' if dc == -1 else 'D' if dr == 1 else 'U'
                attacks.append({'enemy':enemy,'kind':kind,'start':arrive,
                                'end':len(route)-1,'face':face,'standing':target})
            else:
                if typ == 'finish':
                    target = item
                else:
                    choices = [(abs(r-item),abs(r-3),r) for r in range(1,6)
                               if (r,c) not in obstacles]
                    if not choices:
                        raise RuntimeError('No waypoint cell')
                    target = (min(choices)[2],c)
                segment = find_path(route[-1], target, obstacles, cols)
                route.extend(segment[1:])
        return route, attacks

    for _ in range(len(obstacles)+1):
        try:
            route, attacks = compute()
            route.extend(return_via_south(route[-1], obstacles, cols))
            # The final vertex is exactly the start vertex. No position jump
            # occurs when the SVG repeats; the patrol simply begins again.
            assert route[-1] == route[0]
            return days, obstacles, route, attacks
        except RuntimeError:
            optional = [p for p,k in obstacles.items()
                        if k in ('bush','rock','tree')]
            if not optional:
                raise
            obstacles.pop(optional[-1])
    raise RuntimeError('Could not establish connected overworld')


def coordinates(cell):
    r,c = cell
    return LEFT+c*PITCH+CELL/2, TOP+r*PITCH+CELL/2


# Original-game-inspired 13x13 scenery: a limited NES-like palette,
# dark silhouettes and individual leaf/stone pixels.  Unlike the character
# sprites, these are newly drawn tiles, NOT Nintendo image assets.
# Optional authentic scenery PNG/GIF files may be placed in --asset-dir.
SCENERY_PALETTES = {
    'bush': {'1':'#07170a','2':'#075423','3':'#078b29',
             '4':'#18b436','5':'#81d04d','6':'#14361a'},
    'tree': {'1':'#07170a','2':'#054b20','3':'#0a802d',
             '4':'#21ad36','5':'#86d052','6':'#613b1f'},
    'rock': {'1':'#171a12','2':'#4a412f','3':'#7d6748',
             '4':'#b29664','5':'#dcc093','6':'#3e382b'},
    'cave': {'1':'#15160f','2':'#4b3824','3':'#86613a',
             '4':'#b89257','5':'#dfbd78','6':'#070b0c'},
}

# Each line is exactly 13 pixels. Spaces are transparent. The darker rim
# mirrors the outline/contrast of NES overworld scenery; recognizable
# foliage and rocks remain readable at the original calendar cell scale.
SCENERY_PIXELS = {
'bush': (
'    11211    ',
'  112334211  ',
' 12243434221 ',
'1234534333421',
'1243345233421',
'1233443424431',
'1245334533421',
'1224343434331',
' 12334543321 ',
'  123434321  ',
'   1222221   ',
'    16661    ',
'     111     ',
),
'tree': (
'    11111    ',
'  112334211  ',
' 12343434321 ',
'1234534343321',
'1243345234431',
'1245334443431',
'1243435344431',
'1234343433331',
' 12334343221 ',
'  112333221  ',
'    11611    ',
'    16661    ',
'     111     ',
),
'rock': (
'             ',
'    111111   ',
'  113444321  ',
' 12455444321 ',
'1244434333321',
'1245433424321',
'1333333423321',
'1233433323231',
'1223332323221',
' 12223222321 ',
'  111222111  ',
'    11111    ',
'             ',
),
'cave': (
'1234543443231',
'1233443433321',
'1234334544321',
'1234433443321',
'1222266662221',
'1233266663321',
'1244266664421',
'1233266663321',
'1222266662221',
'1233336663321',
'1234336663321',
'1233446663321',
'1222226662221',
),
}


def pixel_tile(rows, palette, x, y):
    """Draw a crisp 13px NES-style tile, merging horizontal pixel runs."""
    if len(rows) != 13 or any(len(row) != 13 for row in rows):
        raise ValueError('Scenery bitmap must be exactly 13 x 13')
    result = []
    for py, row in enumerate(rows):
        i = 0
        while i < 13:
            color = row[i]
            j = i + 1
            while j < 13 and row[j] == color:
                j += 1
            if color != ' ':
                result.append(box(x+i, y+py, j-i, 1, palette[color]))
            i = j
    return ''.join(result)


def scenery(cell, kind):
    cx,cy = coordinates(cell)
    x,y = cx-6.5,cy-6.5
    return pixel_tile(SCENERY_PIXELS[kind],SCENERY_PALETTES[kind],x,y)


def scenery_asset(sprite_assets, kind, cx, cy):
    """Prefer user-supplied original 1986 scenery tiles when present."""
    if kind in sprite_assets:
        # Draw native 16x16 tiles at their ORIGINAL pixel dimensions.
        # The underlying contribution values remain in each date's <title>.
        uri, native_w, native_h = sprite_assets[kind]
        return (f'<image x="{cx-native_w/2:g}" y="{cy-native_h/2:g}" '
                f'width="{native_w:g}" height="{native_h:g}" '
                f'image-rendering="pixelated" href="{uri}"/>')
    # The generator always works without external optional scenery tiles.
    return scenery_at(cx,cy,kind)


def scenery_at(cx,cy,kind):
    return pixel_tile(SCENERY_PIXELS[kind],SCENERY_PALETTES[kind],cx-6.5,cy-6.5)


def rect_intersects(a,b):
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def verify_route(route, obstacles):
    """Check Link's WHOLE bounding box along every animated segment."""
    assert len(route) > 20
    assert not any(p in obstacles for p in route)
    bounds = []
    for cell in obstacles:
        cx,cy = coordinates(cell)
        bounds.append((cx-6.5,cy-6.5,cx+6.5,cy+6.5,cell))
    for a,b in zip(route,route[1:]):
        if abs(a[0]-b[0])+abs(a[1]-b[1]) not in (0,1):
            raise AssertionError(f'Noncardinal movement: {a} to {b}')
        ax,ay=coordinates(a)
        bx,by=coordinates(b)
        for ratio in (0,.25,.5,.75,1):
            x=ax+(bx-ax)*ratio
            y=ay+(by-ay)*ratio
            # Approximate the painted hero footprint, inclusive of the 16px
            # sprite height. Bounds are deliberately conservative.
            hero=(x-7.5,y-8,x+7.5,y+8)
            for x0,y0,x1,y1,object_cell in bounds:
                if rect_intersects(hero,(x0,y0,x1,y1)):
                    raise AssertionError(
                        f'Link overlaps {object_cell} while moving {a}->{b}')


def timed_fade(t, reverse=False, cycle=130.0):
    """Discrete appearance change at a normalized cycle time."""
    values = '0;1;1' if reverse else '1;0;0'
    return (f'<animate attributeName="opacity" values="{values}" '
            f'keyTimes="0;{t:.9f};1" calcMode="discrete" '
            f'dur="{cycle:.4f}s" repeatCount="indefinite"/>')


def travel_direction(a,b):
    dr=b[0]-a[0]
    dc=b[1]-a[1]
    return ('R' if dc==1 else 'L' if dc==-1 else
            'D' if dr==1 else 'U' if dr==-1 else None)


def build_timeline(route, attacks):
    """Produce one synchronized clock for movement, facing and thrusts.

    Turning and attacking are explicit stationary phases. Link cannot skate
    toward an enemy while the sword image is visible. The route returns to
    its origin, with the same sprite direction at the end and beginning.
    """
    by_start={event['start']:event for event in attacks}
    # The initial direction is the first actual movement, not an idle node.
    first_dir=next(travel_direction(a,b) for a,b in zip(route,route[1:])
                   if a!=b)
    frames=[(0.0,route[0],'link_'+first_dir)]
    enemy_hit={}
    shield_blocks=[]
    arrivals={route[0]:0.0}
    t=0.0
    here=route[0]
    facing=first_dir
    i=0
    def add(seconds,cell,state):
        nonlocal t,here
        assert seconds>0
        t+=seconds
        here=cell
        frames.append((t,cell,state))
    while i<len(route)-1:
        if i in by_start:
            ev=by_start[i]
            assert route[i]==ev['standing']
            direction=ev['face']
            if facing!=direction:
                # Stop in place, then visibly face the enemy.
                add(.16,here,'link_'+direction)
                facing=direction
            add(.30,here,'link_'+facing)      # Stop and face the foe.
            # Shield automatically blocks frontal rocks and spears while Link
            # is NOT attacking, just as the NES manual describes. First he
            # faces the ranged foe and holds the normal walking/shield sprite.
            if ev['kind'].startswith(('octorok', 'moblin')):
                guard_start=t
                add(.44,here,'link_'+facing)  # Incoming projectile in flight.
                shield_impact=t
                add(.12,here,'link_'+facing)  # Shield bounce, still stationary.
                shield_blocks.append({
                    'enemy':ev['enemy'], 'kind':ev['kind'],
                    'standing':here, 'face':facing,
                    'start':guard_start, 'impact':shield_impact,
                    'end':t,
                })
            sword_hits = {'octorok_blue':2,'moblin':2,'moblin_blue':3,
                          'leever_red':2,'leever_blue':4,'peahat':2}.get(ev['kind'],1)
            for hit_index in range(sword_hits):
                add(.08,here,'link_thrust_'+facing)   # Extend while stationary.
                add(.30,here,'link_thrust_'+facing)   # NES-style sword thrust.
                if hit_index == sword_hits - 1:
                    enemy_hit[ev['enemy']]=t-.12     # Final blow kills enemy.
                add(.09,here,'link_'+facing)         # Retract while stopped.
                if hit_index < sword_hits-1:
                    add(.24,here,'link_'+facing)     # Blue Octorok survives.
            add(.24,here,'link_'+facing)             # Recovery before walking.
            i=ev['end']
            continue
        nxt=route[i+1]
        if nxt==here:
            # Ignore obsolete placeholder duplicates; real attack pauses
            # are now owned by the timed phases above.
            i+=1
            continue
        move_dir=travel_direction(here,nxt)
        if move_dir is None:
            raise ValueError(f'Non-cardinal segment {here}->{nxt}')
        if facing!=move_dir:
            add(.12,here,'link_'+move_dir)
            facing=move_dir
        add(WALK_SECONDS,nxt,'link_'+facing)
        arrivals.setdefault(nxt,t)
        i+=1
    assert here==route[0], 'Patrol must return to origin'
    if facing!=first_dir:
        add(.12,here,'link_'+first_dir)
    # Short transition holds the initial frame for the next loop.
    add(.04,here,'link_'+first_dir)
    assert frames[-1][1:]==frames[0][1:]
    return {'frames':frames,'total':t,'hits':enemy_hit,'arrivals':arrivals,
            'blocks':shield_blocks, 'starting_face':first_dir}


def choose_respawn(hit, enemy_cell, timeline, duration):
    """Only return after Link has left this enemy's region.

    Zelda NES respawns are area revisits, not continual timer spawns.
    In a fixed-size calendar, horizontal separation stands in for leaving
    the screen. If no safe return is possible, respawn on the next loop.
    """
    for t,cell,state in timeline['frames']:
        if t <= hit+23 or t >= duration-1:
            continue
        if abs(cell[1]-enemy_cell[1]) >= 12:
            return t
    return duration  # Implicitly visible at the beginning of next loop.


def enemy_sprite_name(kind, facing):
    """Pick a real 1986 NES image for the enemy's CURRENT travel direction."""
    if kind.startswith(('octorok', 'moblin')) and facing != 'D':
        return kind + '_' + facing
    return kind


def enemy_patrol(cell, kind, obstacles, link_timeline, cols, hit, respawn, duration):
    """Deterministic 2D roaming on actual contribution cells.

    Static scenery blocks movement. Link's location is checked at the time
    of each move instead of permanently reserving his entire walking route.
    Enemies return to their anchor for scripted sword encounters.
    """
    directions = {(0, 1):'R',(0,-1):'L',(1,0):'D',(-1,0):'U'}
    # Every cell Link EVER visits cannot be reserved permanently. A roaming
    # enemy only avoids Link's position at the matching animation time.
    forbidden=set(obstacles) - {cell}
    frames=link_timeline['frames']
    sample_times=[f[0] for f in frames]
    def link_at(t):
        i=max(0,min(len(frames)-2,bisect_right(sample_times,t)-1))
        t0,p0,_=frames[i];t1,p1,_=frames[i+1]
        if t1<=t0:return p1
        frac=max(0.0,min(1.0,(t-t0)/(t1-t0)))
        return (p0[0]+(p1[0]-p0[0])*frac,
                p0[1]+(p1[1]-p0[1])*frac)
    def safe_move(src,dst,t0,t1):
        for frac in (0,.25,.5,.75,1):
            pos=(src[0]+(dst[0]-src[0])*frac,
                 src[1]+(dst[1]-src[1])*frac)
            hero=link_at(t0+(t1-t0)*frac)
            if abs(pos[0]-hero[0])+abs(pos[1]-hero[1]) < .85:
                return False
        return True
    allowed={cell}
    fringe=[cell]
    for _ in range(4):
        upcoming=[]
        for cur in fringe:
            for n in neighbors(cur,cols):
                if n in forbidden or n in allowed:
                    continue
                if abs(n[0]-cell[0])+abs(n[1]-cell[1])>4:
                    continue
                allowed.add(n);upcoming.append(n)
        fringe=upcoming
    seed=sum((i+1)*ord(ch) for i,ch in enumerate(kind)) + cell[0]*1291+cell[1]*769
    rng=random.Random(seed)
    faster=kind in ('octorok_blue','tektite')
    step_seconds=(.57 if faster else .74 if kind.startswith('octorok') else
                  .82 if kind.startswith('moblin') else
                  .55 if kind=='tektite' else .89 if kind=='tektite_blue' else .68)
    rest_seconds=(.17 if kind.startswith('octorok') else
                  .42 if kind.startswith('moblin') else .35 if kind.startswith('tektite') else .13)
    visited=[]
    events=[]
    def add(t, p, facing='D'):
        # Avoid sub-millisecond duplicate keyframes and preserve the final pose.
        events.append((round(t,5),p,facing))
    def facing(a,b):
        dr,dc=b[0]-a[0],b[1]-a[1]
        return directions.get((0,1 if dc>0 else -1)) if dc else directions.get((1 if dr>0 else -1,0),'D')
    def path_to_anchor(src):
        if src==cell: return []
        q=deque([src]); prior={src:None}
        while q:
            p=q.popleft()
            if p==cell:break
            for n in neighbors(p,cols):
                if n in allowed and n not in prior:
                    prior[n]=p;q.append(n)
        if cell not in prior:
            return []
        path=[];cur=cell
        while cur!=src:
            path.append(cur);cur=prior[cur]
        return path[::-1]
    def phases(begin,end,starting_face):
        t=begin;p=cell;last=None;direction=starting_face
        add(t,p,direction)
        max_cycles=36
        cycles=0
        while cycles<max_cycles:
            cycles+=1
            # Reserve enough time to walk home before an encounter/loop.
            back=path_to_anchor(p)
            spare=end-t-len(back)*step_seconds-0.7
            if spare<=step_seconds+rest_seconds:
                break
            options=[]
            if kind.startswith('tektite'):
                # Short erratic jumps, including diagonal hops. Every landing
                # and intervening crossing must remain free of solid terrain.
                for a in allowed:
                    dr=a[0]-p[0];dc=a[1]-p[1]
                    if 1<=abs(dr)+abs(dc)<=2:
                        if abs(dr)==1 and abs(dc)==1:
                            if (p[0]+dr,p[1]) not in allowed and (p[0],p[1]+dc) not in allowed:
                                continue
                        if abs(dr)==2 and (p[0]+dr//2,p[1]) not in allowed:continue
                        if abs(dc)==2 and (p[0],p[1]+dc//2) not in allowed:continue
                        options.append(a)
            else:
                options=[n for n in neighbors(p,cols) if n in allowed]
            options=[n for n in options if n!=p and
                     t+step_seconds+rest_seconds+len(path_to_anchor(n))*step_seconds+.2 < end]
            options=[n for n in options if safe_move(p,n,t,t+step_seconds)]
            if not options:break
            # Unvisited cells and turning corners score ahead of retracing one
            # segment. Different kinds still have distinct movement rhythms.
            rng.shuffle(options)
            def rank(n):
                new_face=facing(p,n)
                if kind=='leever_red':
                    hero=link_at(t+step_seconds)
                    # Red Leevers advance towards Link when above ground.
                    chase=3.0*(abs(p[0]-hero[0])+abs(p[1]-hero[1])-
                               abs(n[0]-hero[0])-abs(n[1]-hero[1]))
                else:
                    chase=0.0
                return (2 if n!=last else -5) + (1.6 if n not in visited else 0) + \
                       (1.4 if new_face != direction else 0) + chase + rng.random()
            nxt=max(options,key=rank)
            nd=facing(p,nxt)
            add(t,p,nd)
            travel=step_seconds
            if kind.startswith('tektite'):
                # A visible rising and falling hop instead of sliding.
                middle=((p[0]+nxt[0])/2,(p[1]+nxt[1])/2)
                add(t+travel*.5,middle,nd+'H')
            elif kind=='peahat':
                # Flying bob between cells.
                middle=((p[0]+nxt[0])/2,(p[1]+nxt[1])/2)
                add(t+travel*.5,middle,nd+'F')
            t+=travel;p,last=nxt,p;direction=nd
            add(t,p,nd)
            visited.append(p)
            if kind.startswith('leever') and cycles%3==0 and t+.65<end:
                add(t,p,nd+'B')
                t+=.58;add(t,p,nd)
            elif t+rest_seconds<end:
                t+=rest_seconds;add(t,p,nd)
        for nxt in path_to_anchor(p):
            if t+step_seconds>end-.04: break
            if not safe_move(p,nxt,t,t+step_seconds):break
            direction=facing(p,nxt)
            add(t,p,direction);t+=step_seconds;p=nxt
            add(t,p,direction)
        if p != cell:
            raise AssertionError(f'{kind} could not return before encounter: {p} != {cell}')
        add(end,cell,starting_face)
    first_start=.7
    first_end=max(first_start+.02,hit-4.0)
    add(0.0,cell,'D')
    if first_end>first_start+.5:
        phases(first_start,first_end,'D')
    add(hit,cell,'D')
    if respawn<duration-1.8:
        add(respawn,cell,'D')
        second_start=respawn+.7
        second_end=duration-.9
        if second_end>second_start+.5:
            phases(second_start,second_end,'U')
    add(duration,cell,'D')
    # KeyTimes must be strict. All positions are absolute in grid coordinates,
    # except that hop/Fly midpoints may be half-cells.
    merged={t:(p,pose) for t,p,pose in events}
    ordered=[(t,*merged[t]) for t in sorted(merged)]
    assert ordered[0][0]==0 and ordered[-1][0]==round(duration,5)
    return ordered, {'distinct_cells':len(set(visited+[cell])),
                     'directions':sorted(set(face[0] for _,_,face in ordered)),
                     'moves':len(visited),'cells':allowed}


def render_enemy_animation(sprite_assets, kind, cell, schedule, duration):
    """One SVG timebase drives position, facing and hopping."""
    cx,cy=coordinates(cell)
    times=[t/duration for t,_,_ in schedule]
    keytimes=';'.join(f'{v:.10f}' for v in times)
    displacements=[]
    for t,p,pose in schedule:
        dy_bob=-6 if pose.endswith('H') else -3 if pose.endswith('F') else 0
        displacements.append(f'{(p[1]-cell[1])*PITCH:g} {(p[0]-cell[0])*PITCH+dy_bob:g}')
    out=['<g>',f'<animateTransform attributeName="transform" type="translate" '
         f'values="{";".join(displacements)}" keyTimes="{keytimes}" '
         f'calcMode="linear" dur="{duration:.6f}s" repeatCount="indefinite"/>']
    images=sorted({enemy_sprite_name(kind,face[0]) for _,_,face in schedule})
    for sprite in images:
        status=';'.join('1' if enemy_sprite_name(kind,face[0])==sprite and not face.endswith('B') else '0'
                        for _,_,face in schedule)
        out.append(f'<g opacity="{int(enemy_sprite_name(kind,schedule[0][2][0])==sprite and not schedule[0][2].endswith('B'))}">'
                   f'<animate attributeName="opacity" values="{status}" '
                   f'keyTimes="{keytimes}" calcMode="discrete" '
                   f'dur="{duration:.6f}s" repeatCount="indefinite"/>')
        out.append(exact_sprite(sprite_assets,sprite,0,0))
        out.append('</g>')
    out.append('</g>')
    return ''.join(out)


def enemy_visibility(hit, respawn, duration):
    """Stay defeated until Link returns from a distant region."""
    if respawn>=duration:
        # Last value invisible until SVG resets to the next patrol cycle.
        values='1;0;0'
        times=f'0;{hit/duration:.9f};1'
    else:
        values='1;0;1;1'
        times=f'0;{hit/duration:.9f};{respawn/duration:.9f};1'
    return values,times



def ranged_projectiles(kind, schedule, obstacles, anchor, duration, hit, respawn, cols, sprite_assets, link_timeline):
    """NES-style cardinal rocks (Octoroks) and thrown spears (Moblins).

    Firing is pseudo-random but deterministic. Blue Octoroks shoot a little
    more often as a design choice, not a claim about exact NES frame timing.
    """
    if not kind.startswith(('octorok','moblin')):return [],[]
    octorok=kind.startswith('octorok')
    interval=(4.3 if kind=='octorok_blue' else 6.3 if octorok else 7.2)
    travel_time=.85 if octorok else 1.1
    last=-interval
    out=[];shots=[]
    # A scripted shield block is handled separately. Never let unrelated
    # decorative roaming shots pass straight through Link's body.
    hero_frames=link_timeline['frames']
    hero_times=[f[0] for f in hero_frames]
    def hero_xy(at):
        i=max(0,min(len(hero_frames)-2,bisect_right(hero_times,at)-1))
        t0,p0,_=hero_frames[i];t1,p1,_=hero_frames[i+1]
        ratio=0 if t1<=t0 else max(0,min(1,(at-t0)/(t1-t0)))
        x0,y0=coordinates(p0);x1,y1=coordinates(p1)
        return (x0+(x1-x0)*ratio,y0+(y1-y0)*ratio)
    dxdy={'R':(0,1),'L':(0,-1),'D':(1,0),'U':(-1,0)}
    for index,(t,cell,pose) in enumerate(schedule[1:-1],1):
        if t-last<interval or not (1<t<duration-1.5):continue
        if hit-.02<=t<respawn:continue
        if t+travel_time>=hit and t<hit:continue
        if index+1<len(schedule) and schedule[index+1][1]!=cell:continue
        face=pose[0]
        if face not in dxdy:continue
        dr,dc=dxdy[face]
        distance=0
        for steps in range(1,5):
            target=(cell[0]+dr*steps,cell[1]+dc*steps)
            if not (0<=target[0]<7 and 0<=target[1]<cols):break
            if target in obstacles:break
            distance=steps
        if distance<1:continue
        last=t
        cx,cy=coordinates(cell)
        x0,y0=cx+dc*8,cy+dr*8
        x1,y1=x0+dc*PITCH*distance,y0+dr*PITCH*distance
        # Guard against a decorative projectile silently clipping the hero.
        # Planned frontal collisions are instead drawn as shield deflections.
        intersects_hero=False
        for j in range(101):
            fraction=j/100
            hx,hy=hero_xy(t+fraction*travel_time)
            px=x0+(x1-x0)*fraction;py=y0+(y1-y0)*fraction
            if abs(px-hx)<14 and abs(py-hy)<14:
                intersects_hero=True
                break
        if intersects_hero:
            continue
        start=t/duration;stop=(t+travel_time)/duration
        # Position in global SVG space. SVG transform is synchronized to
        # opacity so the projectile appears at the mouth, then advances.
        # Round, 8-bit rock silhouette with dark outer ring, light center.
        # If rock_projectile.png is supplied, render the authentic frame.
        shape=(
            '<g shape-rendering="crispEdges">'
            '<rect x="-2" y="-4" width="4" height="8" fill="#473b31"/>'
            '<rect x="-4" y="-2" width="8" height="4" fill="#473b31"/>'
            '<rect x="-3" y="-3" width="6" height="6" fill="#a89577"/>'
            '<rect x="-2" y="-2" width="4" height="4" fill="#c9b9a0"/>'
            '<rect x="-2" y="-2" width="2" height="2" fill="#e0d1b7"/>'
            '</g>' if octorok else
            '<g shape-rendering="crispEdges">'
            '<rect x="-6" y="-1" width="11" height="2" fill="#795b35"/>'
            '<rect x="4" y="-2" width="3" height="4" fill="#b6b6a5"/>'
            '<rect x="7" y="-1" width="2" height="2" fill="#e6dfc2"/>'
            '</g>')
        if octorok and 'rock_projectile' in sprite_assets:
            shape=exact_sprite(sprite_assets,'rock_projectile',0,0)
        if not octorok:
            if 'spear_projectile' in sprite_assets:
                shape=exact_sprite(sprite_assets,'spear_projectile',0,0)
            rotation={'R':0,'L':180,'U':-90,'D':90}[face]
            shape=f'<g transform="rotate({rotation})">'+shape+'</g>'
        out.append(f'<g data-projectile="{kind}" opacity="0">'
                   f'<animate attributeName="opacity" '
                   f'values="0;1;0;0" keyTimes="0;{start:.9f};{stop:.9f};1" '
                   f'calcMode="discrete" dur="{duration:.6f}s" repeatCount="indefinite"/>'
                   f'<g transform="translate({x0:g} {y0:g})">'
                   f'<animateTransform attributeName="transform" type="translate" additive="replace" '
                   f'values="{x0:g} {y0:g};{x0:g} {y0:g};{x1:g} {y1:g};{x1:g} {y1:g}" '
                   f'keyTimes="0;{start:.9f};{stop:.9f};1" '
                   f'calcMode="linear" dur="{duration:.6f}s" repeatCount="indefinite"/>'
                   +shape+'</g></g>')
        shots.append({'at':t,'facing':face,'origin':cell,'length':distance})
    return out,shots


def shield_deflections(timeline, sprite_assets):
    """Original-style passive shield interception.

    Link must be stationary and face the approaching rock/spear. The shot
    reaches the OUTSIDE of Link's shield, vanishes there, and is rendered
    beneath his sprite so it cannot pass across his body on screen.
    There is no extra magic flash, sword swing, or shield-raising pose.
    """
    duration = timeline['total']
    output = []
    for event in timeline['blocks']:
        enemy_x, enemy_y = coordinates(event['enemy'])
        hero_x, hero_y = coordinates(event['standing'])
        dx, dy = hero_x-enemy_x, hero_y-enemy_y
        mag = (dx*dx + dy*dy)**.5
        if not mag:
            raise AssertionError('Shield block needs a distinct enemy tile')
        ux, uy = dx/mag, dy/mag

        # A rock is round; the spear is rotated to match its approach.
        octorok = event['kind'].startswith('octorok')
        asset = 'rock_projectile' if octorok else 'spear_projectile'
        if asset not in sprite_assets:
            raise ValueError(f'Missing source projectile artwork: {asset}')
        _, native_w, native_h = sprite_assets[asset]
        payload = exact_sprite(sprite_assets,asset,0,0)
        if not octorok:
            if abs(uy) > abs(ux):
                payload = f'<g transform="rotate({90 if uy>0 else -90})">{payload}</g>'
            elif ux < 0:
                payload = f'<g transform="rotate(180)">{payload}</g>'

        # The 15x16 hero sprite reaches about 8px from its center.
        # Leave enough room for the entire projectile at the FRONT of the
        # shield. The extra one-pixel buffer avoids corner overlap.
        projectile_half = (native_w if abs(ux)>abs(uy) else native_h)/2
        if not octorok:
            # The spear is rotated along the direction of travel.
            projectile_half = max(native_w,native_h)/2
        minimum_gap = 8 + projectile_half + 1
        distance = mag - minimum_gap
        if distance < 0:
            # Adjacent sprites can physically touch. Keep the projectile
            # outside the shield rather than passing through Link.
            distance = 0
        contact_x = enemy_x + ux*distance
        contact_y = enemy_y + uy*distance
        # Start at the enemy's center rather than spawning in Link's body.
        origin_x,origin_y = enemy_x,enemy_y
        start = event['start']/duration
        impact = event['impact']/duration
        end = event['end']/duration
        # Very short travel at point-blank range should not last .44s.
        flight_seconds = max(.07, min(.28, distance/75))
        appearance = max(event['start'], event['impact']-flight_seconds)/duration
        assert 0 <= start <= appearance < impact < end <= 1
        phases = f'0;{appearance:.9f};{impact:.9f};{end:.9f};1'
        motion = (f'{origin_x:g} {origin_y:g};{origin_x:g} {origin_y:g};'
                  f'{contact_x:g} {contact_y:g};{contact_x:g} {contact_y:g};'
                  f'{contact_x:g} {contact_y:g}')
        output.append(
            f'<g data-shield-projectile="{event["kind"]}" '
            f'data-shield-face="{event["face"]}" '
            f'data-contact="{contact_x:.6f},{contact_y:.6f}" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;0;0;0" '
            f'keyTimes="{phases}" calcMode="discrete" '
            f'dur="{duration:.6f}s" repeatCount="indefinite"/>'
            f'<g>{payload}<animateTransform attributeName="transform" '
            f'type="translate" values="{motion}" keyTimes="{phases}" '
            f'dur="{duration:.6f}s" calcMode="linear" '
            f'repeatCount="indefinite"/></g></g>')
    return output


def nes_life_hud(width, hearts=3):
    """NES-style LIFE title and native-sized hearts sharing one center."""
    bitmap = (
        '01100110',
        '11111111',
        '11111111',
        '11111111',
        '11111111',
        '01111110',
        '00111100',
        '00011000',
    )
    spacing, heart_width = 16, 8
    # The entire LIFE element has one center, rather than independent x
    # values for its title and hearts.
    center_x = width - 60
    group_width = heart_width + (hearts-1)*spacing
    hearts_x = center_x - group_width/2
    out = [text(center_x, 52, '-LIFE-', 11, '#ed3218',
                'class="label" text-anchor="middle"')]
    for index in range(hearts):
        x = hearts_x + spacing*index
        for yy, row in enumerate(bitmap):
            for xx, bit in enumerate(row):
                if bit == '1':
                    out.append(box(x+xx, 60+yy, 1, 1, '#ec321b'))
    return ''.join(out)


def generate(calendar, sprite_assets):
    days, obstacles, route, attacks = make_map(calendar)
    verify_route(route, obstacles)
    timeline = build_timeline(route, attacks)
    duration = timeline['total']
    cols = len(calendar['weeks'])
    width = LEFT*2+(cols-1)*PITCH+CELL
    height = 312
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {width} {height}" role="img" '
             f'aria-label="Animated Zelda-inspired GitHub contribution calendar">',
             f'<title>The Legend of Commits - {USERNAME}</title>',
             '<style>.pixel{shape-rendering:crispEdges}.label{font-family:monospace;font-weight:bold}</style>',
             box(0,0,width,height,INK),
             box(5,5,width-10,height-10,'none','stroke="#b99a53" stroke-width="2"'),
             box(10,10,width-20,119,'#090c13'),
             title_header(),
             text(22,119,f'@{USERNAME}  |  {calendar["totalContributions"]} CONTRIBUTIONS',10,CREAM,'class="label"')]
    parts.append(nes_life_hud(width, hearts=3))

    # Every real calendar day keeps its green contribution tile and title.
    for c in range(cols):
        for r in range(7):
            x,y=LEFT+c*PITCH,TOP+r*PITCH
            d=days.get((r,c))
            if d:
                color=COLORS.get(d['contributionLevel'],COLORS['NONE'])
                parts.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                             f'fill="{color}" shape-rendering="crispEdges">'
                             f'<title>{escape(d["date"])}: {int(d["contributionCount"])} contributions</title></rect>')
            else:
                parts.append(box(x,y,CELL,CELL,'#17271c'))
    seen_months = set()
    for c, week in enumerate(calendar['weeks']):
        for day in week['contributionDays']:
            month = day['date'][:7]
            if month not in seen_months:
                seen_months.add(month)
                parts.append(text(LEFT+c*PITCH,149,date.fromisoformat(day['date']).strftime('%b').upper(),9,GOLD,'class="label"'))

    # Draw only immobile terrain in the background. Enemy sprites are
    # animated separately after the patrol clock has been constructed.
    ENEMY_KINDS = {'octorok','octorok_blue','moblin','moblin_blue',
                   'tektite','tektite_blue','peahat','leever_red','leever_blue'}
    for cell, kind in sorted(obstacles.items()):
        if kind in ENEMY_KINDS:
            continue
        parts.append('<g class="pixel">'+scenery_asset(sprite_assets, kind, *coordinates(cell))+'</g>')

    # Type-specific enemy movement. Cardinal 2D roaming for Octoroks/Moblins,
    # visible short hopping for Tektites and floating motion for Peahats.
    enemy_reports=[]
    for encounter in attacks:
        cell,kind=encounter['enemy'],encounter['kind']
        hit=timeline['hits'][cell]
        repop=choose_respawn(hit,cell,timeline,duration)
        schedule, stats=enemy_patrol(cell,kind,obstacles,timeline,cols,hit,repop,duration)
        # Ranged foes turn to face Link while shooting their blockable shot.
        guard=next((b for b in timeline['blocks'] if b['enemy']==cell),None)
        if guard:
            enemy_face={'R':'L','L':'R','U':'D','D':'U'}[guard['face']]
            keyed={round(t,5):(p,pose) for t,p,pose in schedule}
            # The roaming enemy has already returned to its anchor.
            keyed[round(guard['start'],5)]=(cell,enemy_face)
            keyed[round(guard['end'],5)]=(cell,enemy_face)
            # Use the same facing up to the defeat frame.
            keyed[round(hit,5)]=(cell,enemy_face)
            schedule=[(t,*keyed[t]) for t in sorted(keyed)]
            assert all(a[0]<b[0] for a,b in zip(schedule,schedule[1:]))
        visible=enemy_visibility(hit,repop,duration)
        cx,cy=coordinates(cell)
        parts.append(f'<g class="pixel" data-enemy="{kind}" '
                     f'data-cell="{cell[0]},{cell[1]}" '
                     f'transform="translate({cx:g} {cy:g})" opacity="1">')
        parts.append(f'<animate attributeName="opacity" '
                     f'values="{visible[0]}" keyTimes="{visible[1]}" '
                     f'calcMode="discrete" dur="{duration:.6f}s" '
                     f'repeatCount="indefinite"/>')
        parts.append(render_enemy_animation(sprite_assets,kind,cell,schedule,duration))
        parts.append('</g>')
        projectiles,shots=ranged_projectiles(kind,schedule,obstacles,cell,duration,hit,repop,cols,sprite_assets,timeline)
        parts.extend(projectiles)
        # The original NES inventory items are used for enemy drops, rather
        # than unrecognizable diamonds or generic modern game loot icons.
        # Classic visible overworld pickups. A rare fairy or clock appears
        # among ordinary hearts, rupees and bombs; keys and Heart Containers
        # are placed separately, not dropped by ordinary overworld foes.
        drops = {
            'octorok': 'heart', 'octorok_blue': 'rupee_blue',
            'moblin': 'bomb', 'moblin_blue': 'clock',
            'tektite': 'heart', 'tektite_blue': 'rupee_blue',
            'peahat': 'fairy', 'leever_red':'rupee', 'leever_blue':'heart',
        }
        item = drops[kind]
        # Place the drop on a walkable cell that Link reaches AFTER the hit.
        # Never leave a pickup trapped in a solid enemy square.
        future=[(tt,cc) for tt,cc,st in timeline['frames']
                if hit+.05<tt<min(duration-.1,hit+30)
                and cc not in obstacles and
                abs(cc[0]-cell[0])+abs(cc[1]-cell[1])<=4]
        future.sort()
        reachable=next(((tt,cc) for tt,cc in future if tt>hit+1.2),None)
        drop_cell=reachable[1] if reachable else None
        drop_x,drop_y=coordinates(drop_cell) if drop_cell else (0,0)
        drop_end=reachable[0] if reachable else hit
        if drop_cell is not None and drop_end>hit:
            start=max(0,hit/duration)
            stop=drop_end/duration
            parts.append(f'<g class="pixel" transform="translate({drop_x:g} {drop_y:g})" opacity="0">'
                         f'<animate attributeName="opacity" values="0;1;0;0" '
                         f'keyTimes="0;{start:.9f};{stop:.9f};1" '
                         f'calcMode="discrete" dur="{duration:.6f}s" repeatCount="indefinite"/>')
            # Item sprites have genuinely transparent backgrounds.
            _,iw,ih = sprite_assets[item]
            if item=='fairy':
                parts.append('<g>')
                parts.append(f'<animateTransform attributeName="transform" '
                             f'type="translate" values="0 0;0 -2;0 0" '
                             f'dur=".85s" repeatCount="indefinite"/>')
            parts.append(exact_sprite(sprite_assets,item,0,0))
            if item=='fairy':
                parts.append('</g>')
            parts.append('</g>')
        enemy_reports.append({'kind':kind,'cell':cell,'patrol':stats,
                              'frames':schedule,'defeated':hit,'respawn':repop,'drop':item,'drop_cell':drop_cell,'shots':shots})

    # Items live INSIDE real contribution squares and disappear only after
    # Link enters their cells. Reserve unique walkable cells on the route.
    # Hearts and fairies are distinct, recognizable NES sprite artwork.
    arrival = timeline['arrivals']
    pickup_names = ('heart', 'rupee', 'bomb', 'fairy', 'rupee_blue',
                    'heart', 'rupee', 'clock', 'rupee_blue')
    hero_cells = [cell for cell in arrival if cell not in obstacles
                  and 2 <= cell[1] <= cols-5]
    hero_cells.sort(key=lambda p: arrival[p])
    pickups = []
    used=set()
    for i, name in enumerate(pickup_names):
        # Spread items throughout the quest rather than bunching them
        # into an unreadable group of icons.
        spot=int((i+1)*len(hero_cells)/(len(pickup_names)+1))
        candidates=sorted(hero_cells,key=lambda p:(abs(hero_cells.index(p)-spot),p))
        cell=next((p for p in candidates if p not in used),None)
        if cell is None:
            continue
        used.add(cell)
        t=arrival[cell]/duration
        if not 0<t<1:
            continue
        cx,cy=coordinates(cell)
        uri,iw,ih=sprite_assets[name]
        # Keep native NES sprite artwork and its repaired transparent background.
        parts.append(f'<g class="pixel" data-pickup="{name}" '
                     f'data-cell="{cell[0]},{cell[1]}" '
                     f'transform="translate({cx:g} {cy:g})" opacity="1">'
                     +timed_fade(t,cycle=duration)
                     )
        if name=='fairy':
            parts.append('<g><animateTransform attributeName="transform" '
                         'type="translate" values="0 0;0 -2;0 0" '
                         'dur=".8s" repeatCount="indefinite"/>')
        parts.append(exact_sprite(sprite_assets,name,0,0))
        if name=='fairy':
            parts.append('</g>')
        parts.append('</g>')
        pickups.append({'item':name,'cell':cell,'collected':arrival[cell]})

    # Triforce is anchored in the *last visited contribution cell*.
    # It appears just before Link arrives and disappears on collection.
    # This is a symbolic overworld finale (NES fragments were in dungeons).
    finish_cell=(3,cols-1)
    if finish_cell not in days or finish_cell in obstacles:
        raise RuntimeError('Triforce goal must be an open contribution cell')
    finish_time=next(t for t,cell,state in timeline['frames'] if cell==finish_cell)
    triforce_cell=finish_cell
    tx,ty=coordinates(triforce_cell)
    visible_at=max(0.001,(finish_time-2)/duration)
    vanish=min(.999999,finish_time/duration)
    if visible_at>=vanish: visible_at=max(.000001,vanish-.001)
    parts.append(f'<g data-item="triforce" '
                 f'data-cell="{triforce_cell[0]},{triforce_cell[1]}" '
                 f'transform="translate({tx:g} {ty:g})" opacity="0">'
                 +f'<animate attributeName="opacity" values="0;1;0;0" '
                 f'keyTimes="0;{visible_at:.9f};{vanish:.9f};1" '
                 f'calcMode="discrete" dur="{duration:.6f}s" repeatCount="indefinite"/>'
                 +exact_sprite(sprite_assets,'triforce',0,0)+'</g>')

    # Shield rocks and spears render BEHIND Link, not over his body.
    # Each also vanishes before crossing the front of his shield.
    parts.extend(shield_deflections(timeline, sprite_assets))

    # All position and sprite frames use the SAME clock. Direction changes
    # occur at stationary cells, and thrust sprites never accompany motion.
    frames=timeline['frames']
    times=[t/duration for t,_,_ in frames]
    assert times[0]==0.0 and abs(times[-1]-1)<1e-9
    assert all(b>a for a,b in zip(times,times[1:]))
    keytimes=';'.join(f'{v:.10f}' for v in times)
    positions=';'.join(f'{coordinates(cell)[0]:g} {coordinates(cell)[1]:g}'
                       for _,cell,_ in frames)
    states=[state for _,_,state in frames]
    parts.append('<g class="pixel" id="link">')
    for name in sorted(set(states)):
        values=';'.join('1' if state==name else '0' for state in states)
        dx=dy=0
        if name.startswith('link_thrust_'):
            _,w,h=sprite_assets[name]
            direction=name[-1]
            if direction=='R': dx=(w-15)/2
            if direction=='L': dx=-(w-15)/2
            if direction=='D': dy=(h-16)/2
            if direction=='U': dy=-(h-16)/2
        parts.append(f'<g data-sprite="{name}" opacity="{int(name==states[0])}">'
                     f'<animate attributeName="opacity" values="{values}" '
                     f'keyTimes="{keytimes}" calcMode="discrete" '
                     f'dur="{duration:.4f}s" repeatCount="indefinite"/>')
        parts.append(exact_sprite(sprite_assets,name,dx,dy))
        parts.append('</g>')
    parts.append('<animateTransform attributeName="transform" type="translate" '
                 f'values="{positions}" keyTimes="{keytimes}" '
                 f'calcMode="linear" dur="{duration:.4f}s" '
                 'repeatCount="indefinite"/></g>')
    parts.append(text(22,298,"IT'S DANGEROUS TO CODE ALONE!",10,GOLD,'class="label"'))
    parts.append('</svg>')
    svg='\n'.join(parts)
    ET.fromstring(svg)
    return svg,{'route':route,'obstacles':obstacles,'attacks':attacks,'days':days,'cols':cols,
                'collision_checked':True,'dimensions':(width,height),
                'timeline':timeline,'enemies':enemy_reports,'pickups':pickups, 'triforce_cell':triforce_cell,
                'shield_blocks':timeline['blocks']}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true',help='Preview without GitHub credentials')
    parser.add_argument('--output',default='img/zelda-contributions.svg')
    parser.add_argument('--asset-dir',default=None,
                        help='Folder containing original NES sprites and scenery')
    parser.add_argument('--require-scenery',action='store_true',
                        help='Fail when any NES scenery or rock-projectile source tile is absent')
    args=parser.parse_args()
    calendar=demo_calendar() if args.demo else get_calendar()
    # Published profile must not silently use hand-drawn stand-in scenery.
    # Demo may use the stand-ins for testing movement before selecting assets.
    strict=args.require_scenery or not args.demo
    svg, report=generate(calendar, load_sprite_assets(args.asset_dir, require_scenery=strict))
    output=Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg,encoding='utf-8')
    print(f'Created {output} with {len(report["route"])} legal steps, '
          f'{len(report["obstacles"])} solid objects, '
          f'{calendar["totalContributions"]} contributions. '
          f'Cycle {report["timeline"]["total"]:.1f}s, seamless closed patrol.')


if __name__=='__main__':
    main()
