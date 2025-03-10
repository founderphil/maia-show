export type WebSocketMessage = {
    type: string;
    pipeline?: string;
    command?: string;
    phase?: string;
    light?: string;
    value?: number;
    userData?: any;
    audio_url?: string;
  };