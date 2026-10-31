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


export interface FareQuote {
    train_schedule_id: number;
    source_station_id: number;
    destination_station_id: number;
    coach_class: CoachClass;
    passengers: number;
    fare_per_passenger: string;
    total_fare: string;
}

export async function getFareQuote(params: {
    scheduleId: number;
    sourceStationId: number;
    destinationStationId: number;
    coachClass: CoachClass;
    passengers?: number;
}): Promise<FareQuote> {
    const query = new URLSearchParams({
        train_schedule_id: String(params.scheduleId),
        source_station_id: String(params.sourceStationId),
        destination_station_id: String(params.destinationStationId),
        coach_class: params.coachClass,
        passengers: String(params.passengers ?? 1),
    });

    const response = await fetch(
        `${API_BASE_URL}/fares/quote?${query.toString()}`,
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to load fare.",
        );
    }

    return data as FareQuote;
}


export type Gender = "MALE" | "FEMALE" | "OTHER";

export type BerthPreference =
    | "NO_PREFERENCE"
    | "LOWER"
    | "MIDDLE"
    | "UPPER"
    | "SIDE_LOWER"
    | "SIDE_UPPER";

export const MAX_PASSENGERS = 6;

export interface PassengerInput {
    passenger_name: string;
    age: number;
    gender: Gender;
    berth_preference: BerthPreference;
}

export interface ConfirmedPassenger extends PassengerInput {
    coach_number: string;
    seat_number: string;
    berth_type: string;
}

// Seat details are not included until the booking is confirmed.
export interface BookingResult {
    booking_id: number;
    booking_reference: string;
    status: string;
    coach_class: CoachClass;
    passengers: PassengerInput[];
    total_amount: string;
    expires_at: string | null;
}

export interface ConfirmedBooking {
    booking_id: number;
    booking_reference: string;
    status: string;
    coach_class: CoachClass;
    confirmed_seats: number;
    passengers: ConfirmedPassenger[];
    total_amount: string;
}

export async function createBooking(params: {
    train: TrainSearchResult;
    coachClass: CoachClass;
    passengers: PassengerInput[];
}): Promise<BookingResult> {
    const response = await fetch(`${API_BASE_URL}/bookings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            train_schedule_id: params.train.schedule_id,
            source_station_id: params.train.source.station_id,
            destination_station_id: params.train.destination.station_id,
            source_stop_order: params.train.source.stop_order,
            destination_stop_order: params.train.destination.stop_order,
            coach_class: params.coachClass,
            passengers: params.passengers,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to create booking.",
        );
    }

    return data as BookingResult;
}

export async function confirmBooking(
    bookingId: number,
): Promise<ConfirmedBooking> {
    const response = await fetch(
        `${API_BASE_URL}/bookings/${bookingId}/confirm`,
        { method: "POST" },
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to confirm booking.",
        );
    }

    return data as ConfirmedBooking;
}




export type BookingStatus =
    | "PENDING"
    | "CONFIRMED"
    | "CANCELLED"
    | "EXPIRED"
    | "WAITLISTED"
    | "PAYMENT_FAILED";

// Seat fields are present only when the booking is CONFIRMED.
export interface BookingDetailsPassenger extends PassengerInput {
    coach_number?: string;
    seat_number?: string;
    berth_type?: string;
}

export interface BookingDetails {
    booking_id: number;
    booking_reference: string;
    status: BookingStatus;
    coach_class: CoachClass;
    total_amount: string;
    expires_at: string | null;
    created_at: string;
    journey_date: string;
    train: {
        train_number: string;
        name: string;
    };
    source: {
        code: string;
        name: string;
        departure_time: string | null;
    };
    destination: {
        code: string;
        name: string;
        arrival_time: string | null;
    };
    distance_km: string | null;
    can_cancel: boolean;
    passengers: BookingDetailsPassenger[];
}

export async function getBooking(reference: string): Promise<BookingDetails> {
    const response = await fetch(
        `${API_BASE_URL}/bookings/${encodeURIComponent(reference)}`,
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to load booking.",
        );
    }

    return data as BookingDetails;
}

export async function cancelBooking(
    reference: string,
): Promise<BookingDetails> {
    const response = await fetch(
        `${API_BASE_URL}/bookings/${encodeURIComponent(reference)}/cancel`,
        { method: "POST" },
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to cancel booking.",
        );
    }

    return data as BookingDetails;
}
