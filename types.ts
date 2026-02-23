
export enum Role {
  USER = 'user',
  MODEL = 'model'
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  isError?: boolean;
}

export interface ProjectFile {
  name: string;
  path: string;
  content: string;
  language: string;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  files: ProjectFile[];
}
