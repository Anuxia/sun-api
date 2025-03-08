from flask import Flask, jsonify
import swisseph as swe
from datetime import datetime, timedelta

app = Flask(__name__)
swe.set_ephe_path('/app/swisseph/ephe')

def calculate_aspect(angle_diff):
    aspects = {
        'Conjunction': (0, 8),
        'Sextile': (60, 6),
        'Square': (90, 8),
        'Trine': (120, 8),
        'Opposition': (180, 8)
    }
    angle_diff = min(angle_diff, 360 - angle_diff)  # Ángulo menor
    for name, (target, orb) in aspects.items():
        if abs(angle_diff - target) <= orb:
            return name
    return None

def get_sign(longitude):
    signs = ['Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo', 'Libra', 'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis']
    return signs[int(longitude // 30)]

def calculate_next_ascendant_change(julian_day, lat, lon):
    current_houses = swe.houses(julian_day, lat, lon)[0]
    current_asc = current_houses[0]
    current_sign = get_sign(current_asc)
    
    # Avanzar el tiempo en incrementos de 1 minuto hasta que cambie el signo
    minutes_ahead = 0
    while True:
        minutes_ahead += 1
        next_julian_day = julian_day + (minutes_ahead / 1440.0)  # 1440 minutos = 1 día
        next_houses = swe.houses(next_julian_day, lat, lon)[0]
        next_asc = next_houses[0]
        next_sign = get_sign(next_asc)
        if next_sign != current_sign:
            break
    
    # Calcular la hora exacta del cambio
    change_time = datetime.utcnow() + timedelta(minutes=minutes_ahead)
    return change_time.isoformat()

@app.route('/sky', methods=['GET'])
def get_sky_map():
    now = datetime.utcnow()
    julday = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
    
    # Posiciones planetarias
    bodies = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO
    }
    sky_map = {}
    for name, body in bodies.items():
        data = swe.calc_ut(julday, body)
        longitude = data[0][0]  # Longitud eclíptica
        sign = get_sign(longitude)
        sky_map[name] = {'longitude': longitude, 'sign': sign}

    # Calcular ascendente y casas (Nueva York)
    lat, lon = 40.71, -74.01  # Nueva York
    houses_data = swe.houses(julday, lat, lon)
    houses = houses_data[0]  # Posiciones de las 12 casas
    ascendant = houses[0]    # El ascendente es la cúspide de la Casa 1
    
    # Formatear casas como diccionario
    houses_dict = {f"House {i+1}": {"longitude": houses[i], "sign": get_sign(houses[i])} for i in range(12)}
    
    # Calcular aspectos
    aspects = {}
    for body1 in sky_map:
        for body2 in sky_map:
            if body1 < body2:  # Evitar duplicados
                diff = abs(sky_map[body1]['longitude'] - sky_map[body2]['longitude'])
                aspect = calculate_aspect(diff)
                if aspect:
                    aspects[f"{body1}-{body2}"] = aspect

    # Calcular próximo cambio del ascendente
    next_change = calculate_next_ascendant_change(julday, lat, lon)
    
    # Agregar datos al resultado
    sky_map['Ascendant'] = {'longitude': ascendant, 'sign': get_sign(ascendant)}
    sky_map['Houses'] = houses_dict
    sky_map['aspects'] = aspects
    sky_map['next_ascendant_change'] = next_change
    sky_map['timestamp'] = now.isoformat()
    
    return jsonify(sky_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
