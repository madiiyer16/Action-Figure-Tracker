import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

const _prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = _prisma;

export const prisma = _prisma;

// Injects canonicalFigureId IS NULL into figure list/count/aggregate queries
// so duplicate (merged) figures never surface in search or browse.
export const canonicalPrisma = _prisma.$extends({
  query: {
    figure: {
      async findMany({ args, query }) {
        args.where = { canonicalFigureId: null, ...args.where };
        return query(args);
      },
      async findFirst({ args, query }) {
        args.where = { canonicalFigureId: null, ...args.where };
        return query(args);
      },
      async count({ args, query }) {
        args.where = { canonicalFigureId: null, ...args.where };
        return query(args);
      },
      async aggregate({ args, query }) {
        args.where = { canonicalFigureId: null, ...args.where };
        return query(args);
      },
    },
  },
});
