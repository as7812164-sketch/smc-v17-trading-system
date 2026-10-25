.class public final synthetic LL/a;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements LL/d$b;


# instance fields
.field public final synthetic a:LL/c;

.field public final synthetic b:Lo/q;

.field public final synthetic c:Ljava/lang/Runnable;

.field public final synthetic d:Ln/f;


# direct methods
.method public synthetic constructor <init>(LL/c;Lo/q;Ljava/lang/Runnable;Ln/f;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, LL/a;->a:LL/c;

    iput-object p2, p0, LL/a;->b:Lo/q;

    iput-object p3, p0, LL/a;->c:Ljava/lang/Runnable;

    iput-object p4, p0, LL/a;->d:Ln/f;

    return-void
.end method


# virtual methods
.method public final a(Z)V
    .locals 4

    .line 1
    iget-object v0, p0, LL/a;->a:LL/c;

    iget-object v1, p0, LL/a;->b:Lo/q;

    iget-object v2, p0, LL/a;->c:Ljava/lang/Runnable;

    iget-object v3, p0, LL/a;->d:Ln/f;

    invoke-static {v0, v1, v2, v3, p1}, LL/c;->d(LL/c;Lo/q;Ljava/lang/Runnable;Ln/f;Z)V

    return-void
.end method
