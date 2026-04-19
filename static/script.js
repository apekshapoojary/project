document.addEventListener('DOMContentLoaded', () => {
    const eventForm = document.getElementById('eventForm');
    const eventList = document.getElementById('eventList');

    let events = [];
    
    // Initial load from backend
    fetchEvents();

    async function fetchEvents() {
        try {
            const response = await fetch('/api/events');
            events = await response.json();
            renderEvents();
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    }

    eventForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get values
        const title = document.getElementById('title').value;
        const date = document.getElementById('date').value;
        const time = document.getElementById('time').value;
        const coordinator = document.getElementById('coordinator').value;
        const venue = document.getElementById('venue').value;

        const newEvent = {
            id: Date.now(),
            title,
            date,
            time,
            coordinator,
            venue
        };

        try {
            const response = await fetch('/api/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newEvent),
            });

            if (response.ok) {
                eventForm.reset();
                await fetchEvents();
            }
        } catch (error) {
            console.error('Error adding event:', error);
        }
    });

    function renderEvents() {
        eventList.innerHTML = '';

        // Sort by date, then by time
        events.sort((a, b) => {
            const dateA = new Date(`${a.date}T${a.time}`);
            const dateB = new Date(`${b.date}T${b.time}`);
            return dateA - dateB;
        });

        if (events.length === 0) {
            eventList.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #94a3b8;">No events scheduled yet.</p>';
            return;
        }

        events.forEach(event => {
            const card = document.createElement('div');
            card.className = 'event-card';
            
            const eventDate = new Date(event.date).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'long',
                day: 'numeric'
            });

            // Display time in 24h IST format
            const timeDisplay = `${event.time} IST`;

            card.innerHTML = `
                <h4>${event.title}</h4>
                <div class="meta-info">
                    <p>📅 <strong>${eventDate}</strong> at <strong>${timeDisplay}</strong></p>
                    <p>📍 ${event.venue}</p>
                    <p>👤 Coord: ${event.coordinator}</p>
                </div>
                <button onclick="deleteEvent(${event.id})" style="margin-top: 15px; padding: 5px 12px; background: #ef4444; font-size: 0.8rem; width: 100%;">Remove</button>
            `;
            eventList.appendChild(card);
        });
    }

    window.deleteEvent = async (id) => {
        if (!confirm('Are you sure you want to remove this event?')) return;
        
        try {
            const response = await fetch(`/api/events/${id}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                await fetchEvents();
            }
        } catch (error) {
            console.error('Error deleting event:', error);
        }
    };
});
