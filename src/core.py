import cloudscraper
import asyncio
import random
import aiohttp
from colorama import *
import json
from datetime import datetime
from . import *
from json.decoder import JSONDecodeError
from requests.exceptions import ConnectionError, Timeout, ProxyError, RequestException, HTTPError

init(autoreset=True)
cfg = read_config()

api_change = cfg.get('api_change', 'cc82f330-6a6d-4deb-a16b-6a335a67ffa7')

class GameSession:
    def __init__(self, acc_data, tgt_score, prxy=None):
        self.b_url = f"https://tonclayton.fun/api/{api_change}"
        self.s_id = None
        self.a_data = acc_data
        self.hdrs = get_headers(self.a_data)
        self.c_score = 0
        self.t_score = tgt_score
        self.inc = 10
        self.pxy = prxy

        self.scraper = cloudscraper.create_scraper()  
        if self.pxy:
            self.scraper.proxies = {
                'http': f'http://{self.pxy}',
                'https': f'http://{self.pxy}',
            }

    @staticmethod
    def fmt_ts(ts):
        dt = datetime.fromisoformat(ts[:-1])
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def proxy_format(proxy):
        if proxy:
            return proxy.split('@')[-1]
        return 'No proxy used'

    async def start(self):
        lg_url = f"{self.b_url}/user/authorization"
        while True:
            resp = self.scraper.post(lg_url, headers=self.hdrs, json={})
            if resp.status_code == 200:
                usr_data = resp.json()
                usr = usr_data.get('user', {})
                log(hju + f"Proxy: {pth}{self.proxy_format(self.pxy)}")
                log(htm + "~" * 38)
                log(bru + f"Username: {pth}{usr.get('username', 'N/A')}")
                log(hju + f"Points: {pth}{usr.get('tokens', 'N/A'):,.0f} {hju}| XP: {pth}{usr.get('current_xp', 'N/A')}")
                log(hju + f"Level: {pth}{usr.get('level', 'N/A')} {hju}| Tickets: {pth}{usr.get('daily_attempts', 0)}")
                await self.check_in()
                break  
            else:
                await asyncio.sleep(2) 
  
    async def check_in(self):
        lg_url = f"{self.b_url}/user/daily-claim"
        resp = self.scraper.post(lg_url, headers=self.hdrs, json={})
        if resp.status_code == 200:
            res = resp.json()
            daily_attempts = res.get('daily_attempts', 0)
            consecutive_days = res.get('consecutive_days', 0)
            log(hju + "Success claim daily check-in")
            log(hju + f"Daily Attempts: {pth}{daily_attempts}{hju}, Consecutive Days: {pth}{consecutive_days}")
        elif resp.status_code == 400:
            log(kng + "You have already checked in today!")
        else:
            log(bru + f"Failed to get check-in data!")

        await asyncio.sleep(2)

    async def run_g(self):
        with open('config.json') as cf:
            g_tickets = json.load(cf).get("game_ticket_to_play", 1)

        for ticket in range(g_tickets):
            game_choice = random.choice(['stack', 'tiles'])
            log(hju + f"Play {pth}{game_choice} {hju}with ticket {pth}{ticket + 1}/{g_tickets}")

            if game_choice == 'stack':
                if not await self.play_stack_game():
                    break
                
            elif game_choice == 'tiles':
                if not await self.play_tiles_game():
                    break
            
            elif game_choice == 'clayball':
                if not await self.play_clay_ball():
                    break

            await countdown_timer(5)

    async def play_stack_game(self):
        if not await self.start_game(f"{self.b_url}/stack/st-game"):
            return False

        self.c_score = 0
        while self.c_score < self.t_score:
            self.c_score += self.inc
            await self.update_score(f"{self.b_url}/stack/update-game", {"score": self.c_score})

        return await self.end_game(f"{self.b_url}/stack/en-game", {"score": self.c_score, "multiplier": 1})

    async def play_tiles_game(self):
        if not await self.start_game(f"{self.b_url}/game/start"):
            return False

        max_tile = 2
        updates = random.randint(7, 10)

        for _ in range(updates):
            payload = {
                "maxTile": max_tile,
                "session_id": self.session_id 
            }
            await self.update_score(f"{self.b_url}/game/save-tile", payload)
            max_tile *= 2

        return await self.end_game(f"{self.b_url}/game/over", {"multiplier": 1})

    async def start_game(self, url):
        resp = self.scraper.post(url, headers=self.hdrs, json={})
        if resp.status_code == 200:
            data = resp.json()  
            self.session_id = data.get('session_id', None) 
            log(bru + "Game started successfully")
            return True
        elif resp.status_code != 200:
            if "attempts are over" in resp.text:
                error_msg = kng + "Game: ticket attempts are over"
                log(f"{error_msg}")
        return False

    async def update_score(self, url, payload):
        resp = self.scraper.post(url, headers=self.hdrs, json=payload)

        if resp.status_code == 200:
            score_type = 'maxTile' if 'maxTile' in payload else 'score'
            log(hju + f"Getting new score: {pth}[ {payload[score_type]} ]", end="\r", flush=True)

        await asyncio.sleep(random.randint(2, 5))

    async def end_game(self, url, payload):
        resp = self.scraper.post(url, headers=self.hdrs, json=payload)

        if resp.status_code == 200:
            res = resp.json()
            log(hju + "Game ended successfully   ")
            log(hju + f"XP Earned: {pth}{res['xp_earned']} | Points: {pth}{res['earn']}")

        await countdown_timer(5)
        return True

    async def play_clay_ball(self):
        if not await self.starts_game("https://tonclayton.fun/clay/start-game"):
            return False
        await countdown_timer(10)

        cl_score = random.randint(40,45)
        payload = {"score": cl_score}
        return await self.ends_game("https://tonclayton.fun/clay/end-game", payload)

    async def starts_game(self, url):
        resp = self.scraper.post(url, headers=self.hdrs, json={})

        if resp.status_code != 200:
            if "attempts are over" in resp.text:
                error_msg = kng + "Game: ticket attempts are over"
                log(f"{error_msg}")
            return False

        log(bru + "Game started successfully")
        return True

    async def ends_game(self, url, payload):
        resp = self.scraper.post(url, headers=self.hdrs, json=payload)

        if resp.status_code == 200:
            res = resp.json()
            log(hju + "Game ended successfully")
            log(hju + f"CL: {pth}{res['cl']} | Multiplier: {pth}{res['multiplier']} | Reward: {pth}{res['reward']}")

        await countdown_timer(5)
        return True
        
    async def cpl_and_clm_tsk(self, tsk_type='daily'):
        if tsk_type == 'daily':
            t_url = f"{self.b_url}/tasks/daily-tasks"
        elif tsk_type == 'default':
            t_url = f"{self.b_url}/tasks/default-tasks"
        elif tsk_type == 'super':
            t_url = f"{self.b_url}/tasks/super-tasks"
        elif tsk_type == 'partner':
            t_url = f"{self.b_url}/tasks/partner-tasks"
        else:
            log(mrh + f"Unknown task type: {tsk_type}")
            return

        await countdown_timer(random.randint(3, 4))
        
        tasks = [] 
        for attempt in range(3):
            resp = self.scraper.get(t_url, headers=self.hdrs)
            if resp.status_code == 200:
                if not resp.text:
                    log(mrh + "Received empty response from the server.")
                    return
                tasks = resp.json()
                break 

            else:
                log(kng + f"Failed decode {tsk_type} {pth}[{attempt + 1}]")
                await asyncio.sleep(3)
                if attempt == 2:
                    return 

        for t in tasks:
            t_id = t['task_id']
            if not t.get('is_completed', False):
                cmp_url = f"{self.b_url}/tasks/complete"
                cmp_resp = self.scraper.post(cmp_url, headers=self.hdrs, json={"task_id": t_id})
                if cmp_resp.status_code == 200:
                    log(hju + f"Completed {pth}{tsk_type}{hju} task: {pth}{t['task']['title']}")
                    wait_time = max(random.randint(4, 6), 1)
                    await countdown_timer(wait_time)
                    clm_url = f"{self.b_url}/tasks/claim"
                    clm_resp = self.scraper.post(clm_url, headers=self.hdrs, json={"task_id": t_id})
                    if clm_resp.status_code == 200:
                        clm_data = clm_resp.json()
                        log(hju + f"Claimed {pth}{t['task']['title']} {hju}| Reward: {pth}{clm_data.get('reward_tokens', '0')}")
                    else:
                        error_message = clm_resp.json().get('error', 'Unknown error')
                        log(mrh + f"Failed to claim {pth}{t_id}: {error_message}")
                else:
                    error_message = cmp_resp.json().get('error', 'Unknown error')
                    log(mrh + f"Failed! Task {pth}{t_id}: {error_message}")
            else:
                log(hju + f"Task {pth}{t['task']['title']} {kng}already completed.")

    async def claim_achievements(self):
        ach_url = f"{self.b_url}/user/achievements/get"
        resp = self.scraper.post(ach_url, headers=self.hdrs, json={})
        if resp.status_code != 200:
            return

        achievements = resp.json()
        claimed_any = False  

        for category in ['friends', 'games', 'stars']:
            for achievement in achievements[category]:
                if achievement['is_completed'] and not achievement['is_rewarded']:
                    lvl = achievement['level']
                    pl = {"type": category, "level": lvl}
                    cl_url = f"{self.b_url}/user/achievements/claim"
                    claim_resp = self.scraper.post(cl_url, headers=self.hdrs, json=pl)
                    if claim_resp.status_code == 200:
                        rwd_data = claim_resp.json()
                        log(hju + f"Achievement {pth}{category} {hju}level {pth}{lvl}{hju}: Reward {pth}{rwd_data['reward']}")
                        claimed_any = True 
                    else:
                        log(kng + f"Can't claim {pth}{category} {kng}achievement lvl {pth}{lvl}")

        if not claimed_any:
            log(kng + "No achievements reward to claim")

async def ld_accs(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def ld_prx(fp):
    with open(fp, 'r') as file:
        return [line.strip() for line in file.readlines()]

async def main():
    tgt_score = random.randint(45, 59)
    use_prxy = cfg.get('use_proxy', False)
    ply_game = cfg.get('play_game', False)
    cpl_tsk = cfg.get('complete_task', False)
    acc_dly = cfg.get('account_delay', 5)
    cntdwn_loop = cfg.get('countdown_loop', 3800)
    prx = await ld_prx('proxies.txt') if use_prxy else []
    accs = await ld_accs("data.txt")

    while True:
        try:
            async with aiohttp.ClientSession():
                for idx, acc in enumerate(accs):
                    log(hju + f"Processing account {pth}{idx + 1} {hju}of {pth}{len(accs)}")
                    prxy = prx[idx % len(prx)] if use_prxy and prx else None
                    game = GameSession(acc, tgt_score, prxy)

                    await game.start()

                    if cpl_tsk:
                        await game.cpl_and_clm_tsk(tsk_type='daily')
                        await game.cpl_and_clm_tsk(tsk_type='partner')
                        await game.cpl_and_clm_tsk(tsk_type='default')
                        await game.cpl_and_clm_tsk(tsk_type='super')

                    if ply_game:
                        await game.run_g()

                    await countdown_timer(3)    
                    await game.claim_achievements()

                    log_line()
                    await countdown_timer(acc_dly)
                await countdown_timer(cntdwn_loop)

        except HTTPError as e:
            log(mrh + f"HTTP error occurred check last.log for detail")
            log_error(f"{str(e)}")
            continue
        except (IndexError, JSONDecodeError) as e:
            log(mrh + f"Data extraction error: {kng}last.log for detail.")
            log_error(f"{str(e)}")
            continue
        except ConnectionError:
            log(mrh + f"Connection lost: {kng}Unable to reach the server.")
            continue
        except Timeout:
            log(mrh + f"Request timed out: {kng}The server is taking too long to respond.")
            continue
        except ProxyError as e:
            log(mrh + f"Proxy error: {kng}Failed to connect through the specified proxy.")
            log_error(f"{str(e)}")
            if "407" in str(e):
                log(bru + f"Proxy authentication failed. Trying another.")
                if prx:
                    proxy = random.choice(prxy)
                    log(bru + f"Switching proxy: {pth}{proxy}")
                else:
                    log(mrh + f"No more proxies available.")
                    break
            else:
                log(htm + f"An error occurred: {htm}{e}")
                break
            continue
        except ValueError as e:
            log(mrh + f"Received non-JSON response check {hju}last.log")
            log_error(f"{str(e)}")
            continue
        except RequestException as e:
            log(mrh + f"An error occurred check {hju}last.log")
            log_error(f"{str(e)}")
            return
