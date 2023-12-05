from PIL import Image, ImageDraw, ImageFont
import time
import random
from Joystick import Joystick

display_width = 240
display_height = 240

# 이미지 로드 함수
def load_image(filename):
    return Image.open(filename)

# 무기 클래스
class Weapon:
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.alive = True

    def move(self):
        self.y -= 10
        if self.y < 0:
            self.alive = False

# 외계인 클래스
class Alien:
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.alive = True

    def move(self):
        self.y += 5
        if self.y > 240:
            self.alive = False

# 아이템 클래스
class Item:
    def __init__(self, image, x, y, item_type):
        self.image = image
        self.x = x
        self.y = y
        self.item_type = item_type
        self.alive = True

    def move(self):
        self.y += 3
        if self.y > 240:
            self.alive = False

# 플레이어 클래스
class Player:
    def __init__(self, image, x, y):
        self.image = image
        self.x = x
        self.y = y
        self.score = 0
        self.lives = 3
        self.special_ready = False
        self.weapons = []

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def fire_weapon(self, weapon_image):
        weapon_x = self.x + self.image.width // 2
        weapon_y = self.y
        self.weapons.append(Weapon(weapon_image, weapon_x, weapon_y))

    def use_special(self):
        if self.special_ready:
            self.special_ready = False
            return True
        return False

# 게임 클래스
class ShootingGame:
    def __init__(self, joystick):
        self.joystick = joystick
        self.player_image = load_image("image/plane.png")
        self.alien_image = load_image("image/alien.png")
        self.background_image = load_image("image/background.png")
        self.life_item_image = load_image("image/life.png")
        self.special_item_image = load_image("image/bomb.png")
        self.weapon_image = load_image("image/bullet.png")
        self.start_image = load_image("image/start_screen.png")
        self.player = Player(self.player_image, 120, 200)
        self.aliens = []
        self.items = []
        self.game_over_flag=False

    def start_screen(self):
        # 시작 화면 이미지 로드 및 표시
        self.joystick.disp.image(self.start_image)
        # 게임 상태 변수 추가
        game_started = False
        # 버튼 입력 대기
        while not game_started:
            if self.joystick.button_A.value == 0:  # 버튼 C가 눌렸을 때만 game_started를 True로 변경
                game_started = True
            time.sleep(0.1)  # 버튼 입력이 있을 때까지 대기
        self.main_loop()  # 게임 메인 루프로 이동

    def main_loop(self):
        while True:
            self.update()
            self.draw()
            time.sleep(0.1)  # 게임 루프 지연

    def update(self):
        # 조이스틱 입력 처리
        dx, dy = 0, 0
        if self.joystick.button_U.value == 0:
            dy = -5
        elif self.joystick.button_D.value == 0:
            dy = 5
        if self.joystick.button_L.value == 0:
            dx = -5
        elif self.joystick.button_R.value == 0:
            dx = 5
        self.player.move(dx, dy)

        # 무기 발사 처리
        if self.joystick.button_A.value == 0:
            self.player.fire_weapon(self.weapon_image)

        current_screen = self.draw()
        for weapon in self.player.weapons:
            weapon.move()
            for alien in self.aliens:
                if self.check_collision(weapon, alien):
                    self.aliens.remove(alien)
                    self.player.score += 10
                    weapon.alive = False
                # 폭발 이미지를 현재 게임 화면에 표시
                    self.show_explosion(alien.x, alien.y, current_screen)  # 수정된 부분
            if not weapon.alive:
                self.player.weapons.remove(weapon)

        if random.randint(0, 20) == 0:
            alien_x = random.randint(0, self.joystick.width - self.alien_image.width)
            alien_y = -self.alien_image.height
            self.aliens.append(Alien(self.alien_image, alien_x, alien_y))

        for alien in self.aliens:
            alien.move()
            if self.check_collision(self.player, alien):
                self.aliens.remove(alien)
                self.player.lives -= 1  # 플레이어 라이프 감소
                if self.player.lives <= 0:
                    self.game_over()  # 게임 오버 처리
                    return  # 게임 오버 상태이므로 update 종료
            if not alien.alive:
                self.aliens.remove(alien)
                if random.randint(0, 5) == 0:
                    item_x = alien.x
                    item_y = alien.y
                    item_type = random.choice(['life', 'special'])
                    item_image = self.life_item_image if item_type == 'life' else self.special_item_image
                    self.items.append(Item(item_image, item_x, item_y, item_type))

        for item in self.items:
            item.move()
            if self.check_collision(self.player, item):
                self.items.remove(item)
                if item.item_type == 'life':
                    self.player.lives += 1
                elif item.item_type == 'special':
                    self.player.special_ready = True

        if self.joystick.button_C.value and self.player.use_special():
            self.aliens.clear()

        if self.game_over_flag:
            self.wait_for_restart()
            
    def game_over(self):
        # 게임 오버 화면을 위한 이미지 객체 생성
        game_over_image = Image.open("image/game_over.png")
        game_over_image = game_over_image.resize((self.joystick.width, self.joystick.height), Image.ANTIALIAS)
        
        # 완성된 이미지를 ST7789 디스플레이에 출력
        self.joystick.disp.image(game_over_image)

        # 게임 오버 상태에서 A 버튼 입력 대기
        while True:
            if self.joystick.button_A.value == 0:
                self.restart_game()  # 게임 재시작
                break
            time.sleep(0.1)

    def restart_game(self):
        # 게임 상태 초기화
        self.player = Player(self.player_image, 120, 200)
        self.aliens = []
        self.items = []
        self.game_over_flag = False
        self.start_screen()  # 시작 화면으로 이동
       
    def show_explosion(self, x, y, current_screen):
        explosion_image = load_image("image/explosion.png").convert("RGBA")
        explosion_size = (explosion_image.width // 2, explosion_image.height // 2)
        explosion_image = explosion_image.resize(explosion_size, Image.ANTIALIAS)
    
    # 폭발 이미지를 외계인이 파괴된 위치에 중심이 오도록 조정
        explosion_position = (x - explosion_size[0] // 2, y - explosion_size[1] // 2)
    
    # 현재 게임 화면에 폭발 이미지를 붙여넣음
        current_screen.paste(explosion_image, explosion_position, explosion_image)
    
    # 폭발이 일어난 화면을 디스플레이에 표시
        self.joystick.disp.image(current_screen, rotation=180)
        time.sleep(0.5)  # 폭발 효과 지속 시간
    
        
    def check_collision(self, obj1, obj2):
        if (obj1.x < obj2.x + obj2.image.width and
            obj1.x + obj1.image.width > obj2.x and
            obj1.y < obj2.y + obj2.image.height and
            obj1.y + obj1.image.height > obj2.y):
            return True
        return False

    def draw(self):
    # 새로운 이미지 객체 생성
        image = Image.new("RGBA", (self.joystick.width, self.joystick.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        background_image = Image.open("image/background.png").convert("RGBA")
        image.paste(background_image, (0, 0), background_image)
    # 배경을 검은색으로 채움
        #draw.rectangle((0, 0, self.joystick.width, self.joystick.height), fill=(0, 0, 0, 255))
        font = ImageFont.truetype("image/project.ttf", 20)
    # 왼쪽 상단에 목숨과 점수 표시
        draw.text((10, 10), f"Lives: {self.player.lives}", font=font, fill=(255, 255, 255))
        draw.text((10, 40), f"Score: {self.player.score}", font=font, fill=(255, 255, 255))    
        
    # 플레이어 이미지 그리기
        player_image = self.player_image.convert("RGBA") if self.player_image.mode != "RGBA" else self.player_image
        image.paste(player_image, (self.player.x, self.player.y), player_image)

    # 외계인 이미지 그리기
        for alien in self.aliens:
            alien_image = self.alien_image.convert("RGBA") if self.alien_image.mode != "RGBA" else self.alien_image
            image.paste(alien_image, (alien.x, alien.y), alien_image)

    # 아이템 이미지 그리기
        for item in self.items:
            item_image = item.image.convert("RGBA") if item.image.mode != "RGBA" else item.image
            image.paste(item_image, (item.x, item.y), item_image)

    # 무기 이미지 그리기
        for weapon in self.player.weapons:
            weapon_image = self.weapon_image.convert("RGBA") if self.weapon_image.mode != "RGBA" else self.weapon_image
            image.paste(weapon_image, (weapon.x, weapon.y), weapon_image)

    # 완성된 이미지를 ST7789 디스플레이에 표시
        self.joystick.disp.image(image)
        return image
        
# 조이스틱 인스턴스 생성
joystick = Joystick()

# 게임 인스턴스 생성 및 시작 화면으로 이동
game = ShootingGame(joystick)
game.start_screen()

