const API_BASE_URL = "http://127.0.0.1:5000/api";

export interface Station {
    id: number;
    code: string;
    name: string;
    city: string;
    state: string;
}

interface StationsResponse {
    count: number;
    stations: Station[];
}

export async function getStations(): Promise<Station[]> {
    const response = await fetch(`${API_BASE_URL}/stations`);

    if (!response.ok) {
        throw new Error("Unable to load stations. Please try again.");
    }

    const data: StationsResponse = await response.json();

    return data.stations;
}


export interface TrainSearchResult {
    schedule_id: number;
    journey_date: string;
    train_number: string;
    name: string;
    running_days: string[];
    source: {
        station_id: number;
        code: string;
        name: string;
        stop_order: number;
        departure_time: string | null;
    };
    destination: {
        station_id: number;
        code: string;
        name: string;
        stop_order: number;
        arrival_time: string | null;
    };
    distance_km: string;
}

interface TrainSearchResponse {
    journey_date: string;
    count: number;
    trains: TrainSearchResult[];
}

export async function searchTrains(params: {
    source: string;
    destination: string;
    date: string;
}): Promise<TrainSearchResponse> {
    const query = new URLSearchParams(params);

    const response = await fetch(
        `${API_BASE_URL}/trains/search?${query.toString()}`,
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Failed to search trains.");
    }

    return data as TrainSearchResponse;
}


export type CoachClass = "SL" | "3A" | "2A" | "1A";

export const COACH_CLASSES: CoachClass[] = ["SL", "3A", "2A", "1A"];

export interface AvailableSeat {
    id: number;
    coach_id: number;
    coach_number: string;
    seat_number: string;
    berth_type: string;
}

interface SeatAvailabilityResponse {
    train_schedule_id: number;
    coach_class: CoachClass;
    source_stop_order: number;
    destination_stop_order: number;
    available_seats: AvailableSeat[];
    count: number;
}

export async function getSeatAvailability(params: {
    scheduleId: number;
    coachClass: CoachClass;
    sourceStopOrder: number;
    destinationStopOrder: number;
}): Promise<SeatAvailabilityResponse> {
    const query = new URLSearchParams({
        coach_class: params.coachClass,
        source_stop_order: String(params.sourceStopOrder),
        destination_stop_order: String(params.destinationStopOrder),
    });

    const response = await fetch(
        `${API_BASE_URL}/availability/${params.scheduleId}?${query.toString()}`,
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to load seat availability.",
        );
    }

    return data as SeatAvailabilityResponse;
}


