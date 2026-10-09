import pyray as rl
import asyncio
import math
import random


def rita_roterad_vag(texture, x, y, rotering, ton=rl.WHITE):
    """Hjälpfunktion för att rita roterad och centrerad väg-textur"""
    w = float(texture.width)
    h = float(texture.height)

    source_rect = rl.Rectangle(0, 0, w, h)
    dest_rect = rl.Rectangle(float(x), float(y), w, h)
    origin = rl.Vector2(w / 2.0, h / 2.0)

    rl.draw_texture_pro(texture, source_rect, dest_rect, origin, float(rotering), ton)


def inom(knapp, p):
    """Kollar om punkten p ligger inom knappen (x, y, bredd, höjd)"""
    return (
        knapp[0] <= p.x <= knapp[0] + knapp[2]
        and knapp[1] <= p.y <= knapp[1] + knapp[3]
    )


async def main():
    # Skapa fönstret (storleksändringsbart)
    rl.set_config_flags(rl.FLAG_WINDOW_RESIZABLE)
    rl.init_window(700, 700, "Mitt Raylib-spel")
    rl.set_window_min_size(400, 400)
    rl.set_target_fps(60)

    # Spelet ritas i fast "virtuell" storlek och skalas sedan till fönstret
    VIRT_B = 1200
    VIRT_H = 1200
    skarm_b = VIRT_B
    skarm_h = VIRT_H
    target = rl.load_render_texture(VIRT_B, VIRT_H)
    rl.set_texture_filter(target.texture, rl.TEXTURE_FILTER_BILINEAR)

    # Ladda in bilder (MÅSTE göras EFTER init_window)
    hus_bild = rl.load_texture("nyast.png")
    fabrik_bild = rl.load_texture("fabrik2.png")
    elverk_bild = rl.load_texture("el.png")
    gras_bild = rl.load_texture("gras2.png")
    road_2_bild = rl.load_texture("road_2.png")
    fiende_bild = rl.load_texture("fiende.png")
    vakt_bild = rl.load_texture("torn.png")  # Bild för vakttorn

    pengar = 400
    cirklar = []
    vag = []
    elverk_pos = rl.Vector2(100, 100)
    elverk_radie = 40.0

    sol = 0
    moon = 0
    hus_x = 600
    hus_y = 400
    hus_radie = 30
    hus_omrode = 60

    fabrik_omrode = 60
    fabrik_radie2 = 60
    fabrik_x = 800
    fabrik_y = 800
    fabrik_pos = rl.Vector2(120, 100)
    fabrik_radie = 40.0
    byggnader_destroyed = 0
    road_2_radie = 30

    # If-sats som kollar kollisionen
    if rl.check_collision_circles(elverk_pos, elverk_radie, fabrik_pos, fabrik_radie):
        pass

    check = 5.0
    colision_el = 60
    colision_fabrik = 60
    colldown = False
    colldown_redan_given = False
    el_colldown = False
    el_colldown_given = False
    lampa = 160
    av = True
    # Dag / Natt & Arbetar-status
    arbetar_vaken = True
    timer = 60.0

    # FIENDER / MONSTER
    fiender = []
    fiende_spawn_timer = 0.0
    fiende_spawn_intervall = 3.0
    BAS_FIENDE_HASTIGHET = 100.0

    # PROJEKTILER FÖR VAKTTORN
    projektiler = []

    # Byggstatus
    valdVäggTyp = None

    # Knappar (x, y, bredd, höjd)
    knapp_cirkel = (10, 90, 180, 40)
    knapp_hus = (10, 180, 180, 40)
    knapp_elverk = (10, 270, 180, 40)
    knapp_road_2 = (10, 360, 180, 40)
    knapp_vakt = (10, 450, 180, 40)
    knapp_hus_zon = (10, 540, 180, 40)
    knapp_fabrik_zon = (10, 630, 180, 40)

    while not rl.window_should_close():
        nuvarande_tid = rl.get_time()
        dt = rl.get_frame_time()

        # Skala så hela spelet ryms i fönstret med bibehållen proportion
        fonster_b = rl.get_screen_width()
        fonster_h = rl.get_screen_height()
        skala = min(fonster_b / VIRT_B, fonster_h / VIRT_H)
        offset_x = (fonster_b - VIRT_B * skala) / 2.0
        offset_y = (fonster_h - VIRT_H * skala) / 2.0

        # Räkna om musen från fönsterkoordinater till spelkoordinater
        rå_mus = rl.get_mouse_position()
        mus_pos = rl.Vector2(
            (rå_mus.x - offset_x) / skala,
            (rå_mus.y - offset_y) / skala,
        )

        # Bestäm rutnätsstorlek baserat på vägbilden
        GRID_STORLEK = float(road_2_bild.width) if road_2_bild.width > 0 else 40.0

        # Beräkna närmsta snäppta grid-position för musen
        snapp_x = round(mus_pos.x / GRID_STORLEK) * GRID_STORLEK
        snapp_y = round(mus_pos.y / GRID_STORLEK) * GRID_STORLEK
        hus_pos = (snapp_x, snapp_y)
        road2_pos = (snapp_x, snapp_y)

        # 1. TIMING & DAG/NATT-CYKEL
        timer -= dt
        if timer <= 0:
            if arbetar_vaken:
                arbetar_vaken = False
                timer = 15.0
                print("Arbetarna sover! Natt-attacken börjar!")
            else:
                arbetar_vaken = True
                timer = 60.0
                fiender.clear()
                projektiler.clear()
                if byggnader_destroyed == 0:
                    pengar += 200
                else:
                    byggnader_destroyed = 0

                print("Arbetarna jobbar! Solen jagar bort fienderna.")

        # 2. FIENDE-LOGIK (ENDAST PÅ NATTEN)
        if not arbetar_vaken:
            av = False

            fiende_spawn_timer += dt
            if fiende_spawn_timer >= fiende_spawn_intervall:
                fiende_spawn_timer = 0.0

                kant = random.choice(["topp", "botten", "vänster", "höger"])
                if kant == "topp":
                    spawn_x, spawn_y = random.randint(0, skarm_b), -20
                elif kant == "botten":
                    spawn_x, spawn_y = random.randint(0, skarm_b), skarm_h + 20
                elif kant == "vänster":
                    spawn_x, spawn_y = -20, random.randint(0, skarm_h)
                else:
                    spawn_x, spawn_y = skarm_b + 20, random.randint(0, skarm_h)

                # Varje fiende får sin egen hastighet
                fiender.append({
                    "x": spawn_x,
                    "y": spawn_y,
                    "radie": 15,
                    "hastighet": BAS_FIENDE_HASTIGHET
                })

            for fiende in fiender[:]:
                # Återställ hastigheten till basvärdet inför kontrollen
                nuvarande_hastighet = BAS_FIENDE_HASTIGHET

                # Kolla om fienden står i lyset från ETT ELVERK
                for byggnad in cirklar:
                    if byggnad["typ"] == "elverk":
                        if rl.check_collision_circles(
                            rl.Vector2(byggnad["x"], byggnad["y"]),
                            lampa,
                            rl.Vector2(fiende["x"], fiende["y"]),
                            fiende["radie"]
                        ):
                            nuvarande_hastighet = 50.0
                            break

                fiende["hastighet"] = nuvarande_hastighet

                # Förflytta fienden mot närmsta byggnad
                if cirklar:
                    närmsta_byggnad = min(
                        cirklar,
                        key=lambda b: math.hypot(
                            b["x"] - fiende["x"], b["y"] - fiende["y"]
                        ),
                    )

                    dx = närmsta_byggnad["x"] - fiende["x"]
                    dy = närmsta_byggnad["y"] - fiende["y"]
                    dist = math.hypot(dx, dy)

                    if dist > 0:
                        fiende["x"] += (dx / dist) * fiende["hastighet"] * dt
                        fiende["y"] += (dy / dist) * fiende["hastighet"] * dt

                    if dist < 30:
                        cirklar.remove(närmsta_byggnad)
                        byggnader_destroyed += 1
                        if fiende in fiender:
                            fiender.remove(fiende)
                        print("En byggnad blev förstörd av ett monster!")

            # 2.5 VAKTTORN SKJUTER PÅ NATTEN
            for byggnad in cirklar:
                if byggnad["typ"] == "vakt":
                    byggnad["skjut_timer"] = byggnad.get("skjut_timer", 0.0) + dt
                    if byggnad["skjut_timer"] >= 0.8:  # Skjuter var 0.8 sekund
                        # Egna variabler så att lambda/list comprehension inte
                        # behöver "fånga" loopvariabeln byggnad
                        torn_x = byggnad["x"]
                        torn_y = byggnad["y"]
                        i_räckvidd = [
                            f for f in fiender
                            if math.hypot(f["x"] - torn_x, f["y"] - torn_y) <= 250.0
                        ]
                        if i_räckvidd:
                            mål = min(
                                i_räckvidd,
                                key=lambda f, tx=torn_x, ty=torn_y: math.hypot(f["x"] - tx, f["y"] - ty)
                            )
                            projektiler.append({
                                "x": torn_x,
                                "y": torn_y,
                                "mål_fiende": mål,
                                "hastighet": 400.0
                            })
                            byggnad["skjut_timer"] = 0.0

            # Uppdatera projektiler
            for p in projektiler[:]:
                if p["mål_fiende"] in fiender:
                    p_dx = p["mål_fiende"]["x"] - p["x"]
                    p_dy = p["mål_fiende"]["y"] - p["y"]
                    p_dist = math.hypot(p_dx, p_dy)

                    if p_dist < 10.0:  # Träff!
                        if p["mål_fiende"] in fiender:
                            fiender.remove(p["mål_fiende"])
                        if p in projektiler:
                            projektiler.remove(p)
                    else:
                        p["x"] += (p_dx / p_dist) * p["hastighet"] * dt
                        p["y"] += (p_dy / p_dist) * p["hastighet"] * dt
                else:
                    if p in projektiler:
                        projektiler.remove(p)

        # 3. MUSKLICK & BYGG-LOGIK / DÖDA FIENDER
        if rl.is_mouse_button_pressed(rl.MOUSE_LEFT_BUTTON):
            klickade_på_knapp = False

            for fiende in fiender[:]:
                if rl.check_collision_circles(
                    mus_pos, 20, rl.Vector2(fiende["x"], fiende["y"]), fiende["radie"]
                ):
                    fiender.remove(fiende)
                    klickade_på_knapp = True
                    break

            if not klickade_på_knapp:
                # Knapp-kontrollerna beräknas alltid (fixar NameError)
                klickade_cirkel_knapp = inom(knapp_cirkel, mus_pos)
                klickade_hus_knapp = inom(knapp_hus, mus_pos)
                klickade_elverk_knapp = inom(knapp_elverk, mus_pos)
                klickade_road_2_knapp = inom(knapp_road_2, mus_pos)
                klickade_vakt_knapp = inom(knapp_vakt, mus_pos)
                klickade_hus_zon_knapp = inom(knapp_hus_zon, mus_pos)
                klickade_fabrik_zon_knapp = inom(knapp_fabrik_zon, mus_pos)

                bygg_pos = rl.Vector2(snapp_x, snapp_y)

                # Börja med de fasta zonerna
                i_hus_område = rl.check_collision_circles(
                    bygg_pos, 1.0, rl.Vector2(hus_x, hus_y), hus_omrode
                )
                i_fabrik_område = rl.check_collision_circles(
                    bygg_pos, 1.0, rl.Vector2(fabrik_x, fabrik_y), fabrik_omrode
                )

                # Kolla sedan zonerna du har placerat själv
                for zon in cirklar:
                    zon_pos = rl.Vector2(zon["x"], zon["y"])

                    if zon["typ"] == "hus_zon":
                        if rl.check_collision_circles(bygg_pos, 1.0, zon_pos, hus_omrode):
                            i_hus_område = True

                    elif zon["typ"] == "fabrik_zon":
                        if rl.check_collision_circles(bygg_pos, 1.0, zon_pos, fabrik_omrode):
                            i_fabrik_område = True

                # 1. HUS -> Får bara placeras i rött område
                if valdVäggTyp == "hus":
                    if i_hus_område:
                        print("Du är i hus område - bra!")
                    else:
                        print("Du är inte i hus område!")
                        valdVäggTyp = None

                # 2. FABRIK OCH ELVERK -> Får bara placeras i blått område
                elif valdVäggTyp in ["cirkel", "elverk"]:
                    if i_fabrik_område:
                        print("Du är i fabrik/elverk område - bra!")
                    else:
                        print("Du är inte i fabrik/elverk område!")
                        valdVäggTyp = None

                if klickade_cirkel_knapp:
                    if pengar >= 50:
                        valdVäggTyp = "cirkel"
                    else:
                        print("För lite pengar för cirkel!")

                elif klickade_hus_knapp:
                    if pengar >= 100:
                        valdVäggTyp = "hus"
                    else:
                        print("För lite pengar för hus!")

                elif klickade_elverk_knapp:
                    if pengar >= 1000:
                        valdVäggTyp = "elverk"
                    else:
                        print("För lite pengar för elverk!")

                elif klickade_road_2_knapp:
                    if pengar >= 50:
                        valdVäggTyp = "road_2"
                    else:
                        print("För lite pengar för väg!")

                elif klickade_vakt_knapp:
                    if pengar >= 1200:
                        valdVäggTyp = "vakt"
                    else:
                        print("För lite pengar för vakttorn!")

                elif klickade_hus_zon_knapp:
                    if pengar >= 75:
                        valdVäggTyp = "hus_zon"
                    else:
                        print("För lite pengar för hus zon!")

                elif klickade_fabrik_zon_knapp:
                    if pengar >= 75:
                        valdVäggTyp = "fabrik_zon"
                    else:
                        print("För lite pengar för fabrik zon!")

                elif valdVäggTyp is not None:
                    if valdVäggTyp in ("hus_zon", "fabrik_zon"):
                        # Zoner får bara inte ligga exakt på en annan zon
                        finns_redan = any(
                            b["x"] == snapp_x and b["y"] == snapp_y
                            for b in cirklar
                            if b["typ"] in ("hus_zon", "fabrik_zon")
                        )
                    else:
                        # Byggnader får ligga ovanpå zoner, men inte på varandra eller vägar
                        finns_redan = any(
                            b["x"] == snapp_x and b["y"] == snapp_y
                            for b in cirklar
                            if b["typ"] not in ("hus_zon", "fabrik_zon")
                        ) or any(v["x"] == snapp_x and v["y"] == snapp_y for v in vag)

                    if valdVäggTyp == "cirkel" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "cirkel",
                            "färg": rl.BLUE,
                            "inkomst": 50,
                        })
                        pengar -= 50
                        valdVäggTyp = None

                    elif valdVäggTyp == "hus" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "hus",
                            "färg": rl.RED,
                            "inkomst": 0,
                        })
                        pengar -= 100
                        valdVäggTyp = None

                    elif valdVäggTyp == "elverk" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "elverk",
                            "färg": rl.YELLOW,
                            "inkomst": 250,
                        })
                        pengar -= 1000
                        valdVäggTyp = None

                    elif valdVäggTyp == "vakt" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "vakt",
                            "färg": rl.ORANGE,
                            "inkomst": 0,
                            "skjut_timer": 0.0,
                        })
                        pengar -= 1200
                        valdVäggTyp = None

                    elif valdVäggTyp == "hus_zon" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "hus_zon",
                        })
                        pengar -= 75
                        valdVäggTyp = None

                    elif valdVäggTyp == "fabrik_zon" and not finns_redan:
                        cirklar.append({
                            "x": snapp_x,
                            "y": snapp_y,
                            "sist_utbetalt": nuvarande_tid,
                            "typ": "fabrik_zon",
                        })
                        pengar -= 75
                        valdVäggTyp = None

                    elif valdVäggTyp == "road_2":
                        if len(vag) == 0:
                            vag.append({
                                "x": snapp_x,
                                "y": snapp_y,
                                "sist_utbetalt": nuvarande_tid,
                                "typ": "road_2",
                                "färg": rl.GRAY,
                                "inkomst": 0,
                                "rotering": 0,
                            })
                            pengar -= 50
                            valdVäggTyp = None
                        else:
                            kan_placera = False
                            ny_x = 0
                            ny_y = 0
                            val_rotering = 0

                            for v in vag:
                                dx = mus_pos.x - v["x"]
                                dy = mus_pos.y - v["y"]

                                if abs(dx) < GRID_STORLEK * 0.6 and -GRID_STORLEK * 1.5 < dy < -GRID_STORLEK * 0.4:
                                    ny_x = v["x"]
                                    ny_y = v["y"] - GRID_STORLEK
                                    val_rotering = 90
                                    kan_placera = True
                                    break
                                elif abs(dx) < GRID_STORLEK * 0.6 and GRID_STORLEK * 0.4 < dy < GRID_STORLEK * 1.5:
                                    ny_x = v["x"]
                                    ny_y = v["y"] + GRID_STORLEK
                                    val_rotering = 90
                                    kan_placera = True
                                    break
                                elif abs(dy) < GRID_STORLEK * 0.6 and -GRID_STORLEK * 1.5 < dx < -GRID_STORLEK * 0.4:
                                    ny_x = v["x"] - GRID_STORLEK
                                    ny_y = v["y"]
                                    val_rotering = 0
                                    kan_placera = True
                                    break
                                elif abs(dy) < GRID_STORLEK * 0.6 and GRID_STORLEK * 0.4 < dx < GRID_STORLEK * 1.5:
                                    ny_x = v["x"] + GRID_STORLEK
                                    ny_y = v["y"]
                                    val_rotering = 0
                                    kan_placera = True
                                    break

                            upptagen_vag = any(b["x"] == ny_x and b["y"] == ny_y for b in vag) or \
                                           any(c["x"] == ny_x and c["y"] == ny_y for c in cirklar)

                            if kan_placera and not upptagen_vag:
                                vag.append({
                                    "x": ny_x,
                                    "y": ny_y,
                                    "sist_utbetalt": nuvarande_tid,
                                    "typ": "road_2",
                                    "färg": rl.GRAY,
                                    "inkomst": 0,
                                    "rotering": val_rotering,
                                })
                                pengar -= 20
                                valdVäggTyp = None
                            else:
                                print("Du kan bara placera vägar intill en befintlig väg!")

        # Kollision mellan elverk och fabrik
        for i in range(len(cirklar)):
            for j in range(i + 1, len(cirklar)):
                b1 = cirklar[i]
                b2 = cirklar[j]

                är_elverk_och_fabrik = (
                    b1["typ"] == "elverk" and b2["typ"] == "cirkel"
                ) or (b1["typ"] == "cirkel" and b2["typ"] == "elverk")

                if är_elverk_och_fabrik:
                    pos1 = rl.Vector2(b1["x"], b1["y"])
                    pos2 = rl.Vector2(b2["x"], b2["y"])

                    if rl.check_collision_circles(
                        pos1, colision_fabrik, pos2, colision_el
                    ):
                        el_colldown = True

        if el_colldown and not el_colldown_given:
            check -= 1.0
            el_colldown_given = True

        # 4. RÄKNA TOTALT ANTAL HUS
        totalt_antal_hus = sum(1 for b in cirklar if b["typ"] == "hus")

        # 4.5 KOLLA OM VÄG FINNS I BÅDE HUS- OCH FABRIK-OMRÅDE (vilken zon som helst)
        # Samla alla zoner: de fasta + de du har placerat själv
        hus_zoner = [rl.Vector2(hus_x, hus_y)]
        fabrik_zoner = [rl.Vector2(fabrik_x, fabrik_y)]

        for z in cirklar:
            if z["typ"] == "hus_zon":
                hus_zoner.append(rl.Vector2(z["x"], z["y"]))
            elif z["typ"] == "fabrik_zon":
                fabrik_zoner.append(rl.Vector2(z["x"], z["y"]))

        finns_vag_i_hus = False
        finns_vag_i_fabrik = False

        for v in vag:
            vag_pos = rl.Vector2(v["x"], v["y"])

            for zon_pos in hus_zoner:
                if rl.check_collision_circles(vag_pos, road_2_radie, zon_pos, hus_omrode):
                    finns_vag_i_hus = True

            for zon_pos in fabrik_zoner:
                if rl.check_collision_circles(vag_pos, road_2_radie, zon_pos, fabrik_omrode):
                    finns_vag_i_fabrik = True

        if finns_vag_i_hus and finns_vag_i_fabrik:
            colldown = True

        # 5. INKOMSTER
        if arbetar_vaken:
            lediga_hus = totalt_antal_hus

            for byggnad in cirklar:
                if byggnad["typ"] == "hus":
                    if nuvarande_tid - byggnad["sist_utbetalt"] >= check:
                        pengar += byggnad["inkomst"]
                        byggnad["sist_utbetalt"] = nuvarande_tid

                elif byggnad["typ"] == "cirkel":
                    KRAV_FABRIK = 3
                    if lediga_hus >= KRAV_FABRIK:
                        lediga_hus -= KRAV_FABRIK
                        if nuvarande_tid - byggnad["sist_utbetalt"] >= check:
                            pengar += byggnad["inkomst"]
                            byggnad["sist_utbetalt"] = nuvarande_tid

                elif byggnad["typ"] == "elverk":
                    KRAV_ELVERK = 5
                    if lediga_hus >= KRAV_ELVERK:
                        lediga_hus -= KRAV_ELVERK
                        if nuvarande_tid - byggnad["sist_utbetalt"] >= check:
                            pengar += byggnad["inkomst"]
                            byggnad["sist_utbetalt"] = nuvarande_tid

        if colldown and not colldown_redan_given:
            check -= 1.0
            print(check)
            colldown_redan_given = True

        # 6. RITA PÅ SKÄRMEN
        rl.begin_texture_mode(target)
        rl.clear_background(rl.RAYWHITE)

        # Gräsbakgrund som fyller hela fönstret
        rl.draw_texture_pro(
            gras_bild,
            rl.Rectangle(0, 0, float(gras_bild.width), float(gras_bild.height)),
            rl.Rectangle(0, 0, float(skarm_b), float(skarm_h)),
            rl.Vector2(0, 0),
            0.0,
            rl.WHITE,
        )

        rl.draw_circle(hus_x, hus_y, hus_omrode, rl.RED)
        rl.draw_circle(fabrik_x, fabrik_y, fabrik_omrode, rl.BLUE)
        if not arbetar_vaken:
            natt_dimning = rl.color_alpha(rl.BLACK, 0.5)
            rl.draw_rectangle(0, 0, skarm_b, skarm_h, natt_dimning)
            el_dimning = rl.color_alpha(rl.YELLOW, 0.3)
            el_dimning2 = rl.color_alpha(rl.YELLOW, 0.7)
            el_dimning3 = rl.color_alpha(rl.YELLOW, 0.5)
        else:
            el_dimning = rl.color_alpha(rl.YELLOW, 0.0)
            el_dimning2 = rl.color_alpha(rl.YELLOW, 0.0)
            el_dimning3 = rl.color_alpha(rl.YELLOW, 0.0)

        for byggnad in cirklar:
            if byggnad["typ"] == "hus":
                rl.draw_texture(
                    hus_bild,
                    int(byggnad["x"]) - hus_bild.width // 2,
                    int(byggnad["y"]) - hus_bild.height // 2,
                    rl.WHITE,
                )
            elif byggnad["typ"] == "elverk":
                rl.draw_circle(
                    int(byggnad["x"]), int(byggnad["y"]), lampa, el_dimning
                )
                rl.draw_circle(
                    int(byggnad["x"]), int(byggnad["y"]), colision_el - 10, el_dimning2
                )
                rl.draw_circle(
                    int(byggnad["x"]), int(byggnad["y"]), colision_el + 20, el_dimning3
                )
                rl.draw_texture(
                    elverk_bild,
                    int(byggnad["x"]) - elverk_bild.width // 2,
                    int(byggnad["y"]) - elverk_bild.height // 2,
                    rl.WHITE,
                )
            elif byggnad["typ"] == "cirkel":
                rl.draw_circle(
                    int(byggnad["x"]), int(byggnad["y"]), colision_fabrik, rl.BLANK
                )
                rl.draw_texture(
                    fabrik_bild,
                    int(byggnad["x"]) - fabrik_bild.width // 2,
                    int(byggnad["y"]) - fabrik_bild.height // 2,
                    rl.WHITE,
                )
            elif byggnad["typ"] == "vakt":
                rl.draw_texture(
                    vakt_bild,
                    int(byggnad["x"]) - vakt_bild.width // 2,
                    int(byggnad["y"]) - vakt_bild.height // 2,
                    rl.WHITE,
                )
            elif byggnad["typ"] == "hus_zon":
                rl.draw_circle(int(byggnad["x"]), int(byggnad["y"]), float(hus_omrode), rl.RED)
            elif byggnad["typ"] == "fabrik_zon":
                rl.draw_circle(int(byggnad["x"]), int(byggnad["y"]), float(fabrik_omrode), rl.BLUE)

        for byggnad in vag:
            if byggnad["typ"] == "road_2":
                rita_roterad_vag(
                    road_2_bild,
                    byggnad["x"],
                    byggnad["y"],
                    byggnad.get("rotering", 0),
                )

        for fiende in fiender:
            rl.draw_circle(
                int(fiende["x"]), int(fiende["y"]), fiende["radie"], rl.BLANK
            )
            rl.draw_circle(
                int(fiende["x"]), int(fiende["y"]), fiende["radie"] - 4, rl.BLANK
            )
            rl.draw_texture(fiende_bild, int(fiende["x"]), int(fiende["y"]), rl.WHITE)

        # Rita skott / projektiler från vakttorn
        for p in projektiler:
            rl.draw_circle(int(p["x"]), int(p["y"]), 4, rl.BLACK)

        # Förhandsvisning vid bygge
        if valdVäggTyp == "hus":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), hus_radie, rl.GRAY
            )
            rl.draw_texture(
                hus_bild,
                int(snapp_x) - hus_bild.width // 2,
                int(snapp_y) - hus_bild.height // 2,
                rl.WHITE,
            )
        elif valdVäggTyp == "cirkel":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), fabrik_radie2, rl.RED
            )
            rl.draw_circle(
                int(snapp_x), int(snapp_y), colision_el, rl.LIGHTGRAY
            )
            rl.draw_texture(
                fabrik_bild,
                int(snapp_x) - fabrik_bild.width // 2,
                int(snapp_y) - fabrik_bild.height // 2,
                rl.WHITE,
            )
        elif valdVäggTyp == "elverk":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), fabrik_radie2, rl.RED
            )
            rl.draw_circle(
                int(snapp_x), int(snapp_y), colision_el, rl.LIGHTGRAY
            )
            rl.draw_texture(
                elverk_bild,
                int(snapp_x) - elverk_bild.width // 2,
                int(snapp_y) - elverk_bild.height // 2,
                rl.WHITE,
            )
        elif valdVäggTyp == "hus_zon":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), hus_omrode, rl.RED
            )
            rl.draw_circle(
                int(snapp_x), int(snapp_y), hus_omrode, rl.LIGHTGRAY)
        elif valdVäggTyp == "fabrik_zon":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), fabrik_omrode, rl.RED
            )
            rl.draw_circle(
                int(snapp_x), int(snapp_y), fabrik_omrode, rl.LIGHTGRAY)
        elif valdVäggTyp == "vakt":
            rl.draw_circle(
                int(snapp_x), int(snapp_y), 250, rl.color_alpha(rl.RED, 0.2)  # Visa räckvidd
            )
            rl.draw_texture(
                vakt_bild,
                int(snapp_x) - vakt_bild.width // 2,
                int(snapp_y) - vakt_bild.height // 2,
                rl.WHITE,
            )
        elif valdVäggTyp == "road_2":
            for v in vag:
                rl.draw_circle_v(rl.Vector2(road2_pos[0], road2_pos[1]), road_2_radie, rl.RED)
                dx = mus_pos.x - v["x"]
                dy = mus_pos.y - v["y"]

                if abs(dx) < GRID_STORLEK * 0.6 and -GRID_STORLEK * 1.5 < dy < -GRID_STORLEK * 0.4:
                    rita_roterad_vag(road_2_bild, v["x"], v["y"] - GRID_STORLEK, 90, rl.GRAY)
                    break
                elif abs(dx) < GRID_STORLEK * 0.6 and GRID_STORLEK * 0.4 < dy < GRID_STORLEK * 1.5:
                    rita_roterad_vag(road_2_bild, v["x"], v["y"] + GRID_STORLEK, 90, rl.GRAY)
                    break
                elif abs(dy) < GRID_STORLEK * 0.6 and -GRID_STORLEK * 1.5 < dx < -GRID_STORLEK * 0.4:
                    rita_roterad_vag(road_2_bild, v["x"] - GRID_STORLEK, v["y"], 0, rl.GRAY)
                    break
                elif abs(dy) < GRID_STORLEK * 0.6 and GRID_STORLEK * 0.4 < dx < GRID_STORLEK * 1.5:
                    rita_roterad_vag(road_2_bild, v["x"] + GRID_STORLEK, v["y"], 0, rl.GRAY)
                    break
            else:
                if len(vag) == 0:
                    rita_roterad_vag(road_2_bild, snapp_x, snapp_y, 0, rl.GRAY)

        # Sol & Måne (börjar om när de nått fönstrets kant)
        if arbetar_vaken:
            rl.draw_circle(int(sol) % skarm_b, 10, 100, rl.YELLOW)
            moon = 0
        else:
            rl.draw_circle(int(moon) % skarm_b, 10, 100, rl.LIGHTGRAY)
            sol = 0

        # Knappar
        färg_cirkel = rl.GREEN if valdVäggTyp == "cirkel" else rl.GRAY
        rl.draw_rectangle(
            knapp_cirkel[0], knapp_cirkel[1], knapp_cirkel[2], knapp_cirkel[3], färg_cirkel
        )
        rl.draw_text("Factory 50$", knapp_cirkel[0] + 20, knapp_cirkel[1] + 10, 18, rl.WHITE)

        färg_hus = rl.GREEN if valdVäggTyp == "hus" else rl.GRAY
        rl.draw_rectangle(knapp_hus[0], knapp_hus[1], knapp_hus[2], knapp_hus[3], färg_hus)
        rl.draw_text("House 100$", knapp_hus[0] + 35, knapp_hus[1] + 10, 18, rl.WHITE)

        färg_elverk = rl.GREEN if valdVäggTyp == "elverk" else rl.GRAY
        rl.draw_rectangle(
            knapp_elverk[0], knapp_elverk[1], knapp_elverk[2], knapp_elverk[3], färg_elverk
        )
        rl.draw_text("Powerplant 1000$", knapp_elverk[0] + 25, knapp_elverk[1] + 10, 18, rl.WHITE)

        färg_road_2 = rl.GREEN if valdVäggTyp == "road_2" else rl.GRAY
        rl.draw_rectangle(
            knapp_road_2[0], knapp_road_2[1], knapp_road_2[2], knapp_road_2[3], färg_road_2
        )
        rl.draw_text("Road 50$", knapp_road_2[0] + 35, knapp_road_2[1] + 10, 18, rl.WHITE)

        färg_vakt = rl.GREEN if valdVäggTyp == "vakt" else rl.GRAY
        rl.draw_rectangle(
            knapp_vakt[0], knapp_vakt[1], knapp_vakt[2], knapp_vakt[3], färg_vakt
        )
        rl.draw_text("Watchtower 1200$", knapp_vakt[0] + 15, knapp_vakt[1] + 10, 18, rl.WHITE)

        rl.draw_rectangle(
            knapp_hus_zon[0], knapp_hus_zon[1], knapp_hus_zon[2], knapp_hus_zon[3], rl.RED
        )
        rl.draw_text("House zone 75$", knapp_hus_zon[0] + 15, knapp_hus_zon[1] + 10, 18, rl.WHITE)

        rl.draw_rectangle(
            knapp_fabrik_zon[0], knapp_fabrik_zon[1], knapp_fabrik_zon[2], knapp_fabrik_zon[3], rl.BLUE
        )
        rl.draw_text("Factory zone 75$", knapp_fabrik_zon[0] + 15, knapp_fabrik_zon[1] + 10, 18, rl.WHITE)

        # UI Text & Status
        rl.draw_text(f"$: {pengar}", 10, 10, 30, rl.DARKGREEN)

        sol += 0.33
        moon += 1.3
        rl.end_texture_mode()

        # Rita den skalade bilden i fönstret (svarta kanter vid annan proportion)
        rl.begin_drawing()
        rl.clear_background(rl.BLACK)
        rl.draw_texture_pro(
            target.texture,
            rl.Rectangle(0, 0, float(VIRT_B), -float(VIRT_H)),  # minus = vänd rätt
            rl.Rectangle(offset_x, offset_y, VIRT_B * skala, VIRT_H * skala),
            rl.Vector2(0, 0),
            0.0,
            rl.WHITE,
        )
        rl.end_drawing()

        await asyncio.sleep(0)

    # Stäng fönstret och frigör minne
    rl.unload_texture(hus_bild)
    rl.unload_texture(fabrik_bild)
    rl.unload_texture(elverk_bild)
    rl.unload_texture(gras_bild)
    rl.unload_texture(road_2_bild)
    rl.unload_texture(fiende_bild)
    rl.unload_texture(vakt_bild)
    rl.unload_render_texture(target)
    rl.close_window()


# Kör koden asynkront
asyncio.run(main())