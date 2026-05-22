import L from 'leaflet';
import { getColor } from '../utils/map-helpers';

let map = null;

export function renderMap() {
    return `
    <section class="widget-card col-span-6 row-span-2">
        <h3 class="widget-title">Attacker origin</h3>
        <div class="map-wrapper">
            <div id="map-container"></div>
        </div>
    </section>   
    `;
}

export function initAttackerMap(attackerData) {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;

    if (map !== null) {
        map.remove();
        map = null;
    }

    map = L.map(mapContainer, { center: [20, 0], zoom: 2, minZoom: 1.5 });

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);

    if (attackerData && Array.isArray(attackerData)) {
        attackerData.forEach(row => {
            L.circleMarker([row.lat, row.lon], {
                radius: Math.min(row.count * 0.3, 30),
                color: getColor(row.count),
                fillColor: getColor(row.count),   
                fillOpacity: 0.5,
                weight: 1
            })
            .addTo(map)
            .bindPopup(`<b>IP:</b> ${row.ip}<br><b>Total Attacks:</b> ${row.count}`);
        });
    }
}
