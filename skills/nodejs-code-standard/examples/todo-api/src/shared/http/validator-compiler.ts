import { Ajv, type Options } from 'ajv';
import addFormatsModule from 'ajv-formats';
import type { FastifySchemaCompiler } from 'fastify';

const addFormats = addFormatsModule as unknown as typeof addFormatsModule.default;

const shared: Options = { allErrors: false, useDefaults: true, strict: true };

const bodyAjv = new Ajv({ ...shared, coerceTypes: false, removeAdditional: false });
const urlAjv = new Ajv({ ...shared, coerceTypes: 'array', removeAdditional: false });
addFormats(bodyAjv);
addFormats(urlAjv);

export const validatorCompiler: FastifySchemaCompiler<object> = ({ schema, httpPart }) =>
  httpPart === 'body' ? bodyAjv.compile(schema) : urlAjv.compile(schema);
