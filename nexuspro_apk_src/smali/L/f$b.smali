.class LL/f$b;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = LL/f;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0xa
    name = "b"
.end annotation


# instance fields
.field public final a:Z

.field public final b:Z


# direct methods
.method private constructor <init>(ZZ)V
    .locals 0

    .line 2
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 3
    iput-boolean p1, p0, LL/f$b;->a:Z

    .line 4
    iput-boolean p2, p0, LL/f$b;->b:Z

    return-void
.end method

.method synthetic constructor <init>(ZZLL/f$a;)V
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, LL/f$b;-><init>(ZZ)V

    return-void
.end method
