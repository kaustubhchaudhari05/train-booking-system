// Proxied to Flask by the Vite dev server (see vite.config.ts), so the
// login cookies stay first-party.
const API_BASE_URL = "/api";

// Fired when the API answers 401, so the app can drop the stale user.
export const AUTH_EXPIRED_EVENT = "auth:expired";

function csrfToken() {
    const match = document.cookie.match(
        /(?:^|;\s*)csrf_access_token=([^;]+)/,
    );
    return match ? decodeURIComponent(match[1]) : "";
}

// All API calls go through here. The JWT travels in an httpOnly cookie;
// writes also send the CSRF token from its readable companion cookie.
async function apiFetch(path: string, init: RequestInit = {}) {
    const method = (init.method ?? "GET").toUpperCase();
    const headers = new Headers(init.headers);

    if (method !== "GET") {
        headers.set("X-CSRF-TOKEN", csrfToken());
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers,
        credentials: "same-origin",
    });

    if (response.status === 401) {
        window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }

    return response;
}

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
    const response = await apiFetch(`/stations`);

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

    const response = await apiFetch(
        `/trains/search?${query.toString()}`,
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
    waitlist_count: number;
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

    const response = await apiFetch(
        `/availability/${params.scheduleId}?${query.toString()}`,
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

    const response = await apiFetch(
        `/fares/quote?${query.toString()}`,
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

export type PassengerStatus = "ACTIVE" | "WAITLISTED" | "CANCELLED";

// Seat fields are present only for seated passengers of a confirmed
// booking. waitlist_position is set only for waitlisted passengers whose
// booking is CONFIRMED or WAITLISTED (i.e. who are in the queue).
export interface BookedPassenger extends PassengerInput {
    id: number;
    status: PassengerStatus;
    waitlist_position: number | null;
    coach_number?: string;
    seat_number?: string;
    berth_type?: string;
}

// Seat details are not included until the booking is confirmed.
export interface BookingResult {
    booking_id: number;
    booking_reference: string;
    status: BookingStatus;
    coach_class: CoachClass;
    passengers: BookedPassenger[];
    total_amount: string;
    expires_at: string | null;
}

export interface ConfirmedBooking {
    booking_id: number;
    booking_reference: string;
    status: BookingStatus;
    coach_class: CoachClass;
    confirmed_seats: number;
    passengers: BookedPassenger[];
    total_amount: string;
}

export async function createBooking(params: {
    train: TrainSearchResult;
    coachClass: CoachClass;
    passengers: PassengerInput[];
}): Promise<BookingResult> {
    const response = await apiFetch(`/bookings`, {
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

export interface PaymentOrder {
    payment_id: number;
    key_id: string;
    order_id: string;
    // In paise, as Razorpay Checkout expects.
    amount: number;
    currency: string;
    booking_reference: string;
    expires_at: string;
    hold_seconds_left: number;
}

export async function createPaymentOrder(
    bookingId: number,
): Promise<PaymentOrder> {
    const response = await apiFetch(`/payments/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ booking_id: bookingId }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to start payment.",
        );
    }

    return data as PaymentOrder;
}

// What Razorpay Checkout hands to its success handler.
export interface RazorpayCheckoutResult {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
}

// The server checks the signature and the payment with Razorpay before
// confirming the booking; a Checkout success alone proves nothing.
export async function verifyPayment(
    result: RazorpayCheckoutResult,
): Promise<ConfirmedBooking> {
    const response = await apiFetch(`/payments/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(result),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to verify payment.",
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

export interface BookingDetailsPassenger extends BookedPassenger {
    can_cancel: boolean;
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
    const response = await apiFetch(
        `/bookings/${encodeURIComponent(reference)}`,
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to load booking.",
        );
    }

    return data as BookingDetails;
}

// The name must match a passenger in the booking exactly (case-sensitive).
export async function cancelPassenger(
    reference: string,
    passengerName: string,
): Promise<BookingDetails> {
    const response = await apiFetch(
        `/bookings/${encodeURIComponent(reference)}` +
            "/cancel-passenger",
        {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ passenger_name: passengerName }),
        },
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to cancel passenger.",
        );
    }

    return data as BookingDetails;
}


export interface User {
    id: number;
    name: string;
    email: string;
}

interface UserResponse {
    user: User | null;
}

async function authRequest(path: string, body?: object): Promise<User | null> {
    const response = await apiFetch(`/auth/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body ?? {}),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || data.error || "Request failed.");
    }

    return (data as UserResponse).user;
}

// Returns null when nobody is logged in.
export async function getCurrentUser(): Promise<User | null> {
    const response = await apiFetch("/auth/me");

    if (!response.ok) {
        throw new Error("Unable to check your login. Please try again.");
    }

    const data: UserResponse = await response.json();
    return data.user;
}

export async function login(email: string, password: string) {
    return (await authRequest("login", { email, password })) as User;
}

export async function register(params: {
    name: string;
    email: string;
    password: string;
}) {
    return (await authRequest("register", params)) as User;
}

export async function logout() {
    await authRequest("logout");
}

export interface BookingListItem {
    booking_reference: string;
    status: BookingStatus;
    coach_class: CoachClass;
    total_amount: string;
    journey_date: string;
    created_at: string;
    train: {
        train_number: string;
        name: string;
    };
    source_code: string;
    destination_code: string;
    passenger_count: number;
}

export async function getMyBookings(): Promise<BookingListItem[]> {
    const response = await apiFetch("/bookings");

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.message || data.error || "Failed to load your bookings.",
        );
    }

    return (data as { bookings: BookingListItem[] }).bookings;
}
