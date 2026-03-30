export function toPtBrDate(input: string): string {
  const date = new Date(input);
  return new Intl.DateTimeFormat('pt-BR').format(date);
}
