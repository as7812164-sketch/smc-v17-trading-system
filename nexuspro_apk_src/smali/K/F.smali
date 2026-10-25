.class public final synthetic LK/F;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field public final synthetic a:LK/I;

.field public final synthetic b:Lo/q;

.field public final synthetic c:LL/e;

.field public final synthetic d:Ljava/lang/Runnable;


# direct methods
.method public synthetic constructor <init>(LK/I;Lo/q;LL/e;Ljava/lang/Runnable;)V
    .locals 0

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    iput-object p1, p0, LK/F;->a:LK/I;

    iput-object p2, p0, LK/F;->b:Lo/q;

    iput-object p3, p0, LK/F;->c:LL/e;

    iput-object p4, p0, LK/F;->d:Ljava/lang/Runnable;

    return-void
.end method


# virtual methods
.method public final run()V
    .locals 4

    .line 1
    iget-object v0, p0, LK/F;->a:LK/I;

    iget-object v1, p0, LK/F;->b:Lo/q;

    iget-object v2, p0, LK/F;->c:LL/e;

    iget-object v3, p0, LK/F;->d:Ljava/lang/Runnable;

    invoke-static {v0, v1, v2, v3}, LK/I;->a(LK/I;Lo/q;LL/e;Ljava/lang/Runnable;)V

    return-void
.end method
