export interface PageRequest {
  readonly limit: number;
  readonly offset: number;
}

export interface Page<T> extends PageRequest {
  readonly items: readonly T[];
  readonly total: number;
}
