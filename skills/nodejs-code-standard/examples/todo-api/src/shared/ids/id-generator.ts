import { randomUUID } from 'node:crypto';

export type IdGenerator = () => string;

export const uuidGenerator: IdGenerator = () => randomUUID();
