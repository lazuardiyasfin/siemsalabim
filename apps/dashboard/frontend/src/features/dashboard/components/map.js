import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { getColor } from '../utils/map-helpers';

let map = null;
const markersMap = new Map();
const ipCounts = new Map();

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

export function initAttackerMap() {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;

    if (map !== null) {
        map.remove();
        map = null;
    }

    markersMap.clear();
    ipCounts.clear();

    map = L.map(mapContainer, { center: [20, 0], zoom: 2, minZoom: 1.5 });

    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
}

export function addAttackerLocation(lat, lon, ip) {
    if (!map || !lat || !lon) return;

    const count = (ipCounts.get(ip) || 0) + 1;
    ipCounts.set(ip, count);

    if (markersMap.has(ip)) {
        const marker = markersMap.get(ip);
        marker.setRadius(Math.min(count * 0.3, 30));
        marker.setStyle({
            color: getColor(count),
            fillColor: getColor(count)
        });
        marker.setPopupContent(`<b>IP:</b> ${ip}<br><b>Total Attacks:</b> ${count}`);
    } else {
        const marker = L.circleMarker([lat, lon], {
            radius: Math.min(count * 0.3, 30),
            color: getColor(count),
            fillColor: getColor(count),   
            fillOpacity: 0.5,
            weight: 1
        })
        .addTo(map)
        .bindPopup(`<b>IP:</b> ${ip}<br><b>Total Attacks:</b> ${count}`);

        markersMap.set(ip, marker);
    }
}